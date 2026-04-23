<script lang="ts" module>
	function focusInput(node: HTMLInputElement) {
		node.focus();
		node.select();
	}
</script>

<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as echarts from 'echarts';
	import type { ChartAxis } from '../state.svelte';
	import { viewerState } from '../state.svelte';
	import { convertValue } from '../units';

	let { axis, index }: { axis: ChartAxis; index: number } = $props();

	let chartContainer: HTMLDivElement;
	let chartInstance: echarts.ECharts | null = null;
	let isMounted = $state(false);
	let resizeObserver: ResizeObserver | null = null;
	let zoomTimeout: ReturnType<typeof setTimeout> | undefined;

	let editingYLabel = $state(false);
	let editYLabelText = $state('');
	let editYLabelPos = $state({ x: 0, y: 0 });
	let isCopying = $state(false);

	// Watch data and bounds to update chart
	$effect(() => {
		if (isMounted && chartInstance && !viewerState.loading) {
			updateChart();
		}
	});

	function updateChart() {
		if (!chartInstance) return;

		const series: any[] = [];
		const legendData: string[] = [];
		const uniqueUnits = new Set<string>();
		const refDate = new Date(Date.UTC(viewerState.startYear, 0, 1, 0, 0, 0));

		// Add global background series to preserve full year shape in dataZoom
		if (axis.variables.length > 0) {
			const firstVar = axis.variables[0];
			const globalInfo = viewerState.globalChartData[axis.id]?.[firstVar];
			if (globalInfo && globalInfo.x.length > 0) {
				const points = globalInfo.x.map((x, i) => {
					return [x, globalInfo.y[i]];
				});
				series.push({
					name: 'BackgroundDataZoom',
					type: 'line',
					sampling: 'lttb',
					large: true,
					largeThreshold: 600,
					data: points,
					showSymbol: false,
					tooltip: { show: false },
					lineStyle: { opacity: 0 },
					itemStyle: { opacity: 0 },
					animation: false,
					hoverAnimation: false,
					silent: true
				});
			}
		}

		// Compile main series
		axis.variables.forEach((varName, idx) => {
			const dataInfo = viewerState.chartData[axis.id]?.[varName];
			if (dataInfo) {
				const varDef = viewerState.availableVariables.find((v) => v.raw_col === varName);
				const nativeUnit = varDef ? varDef.unit : '';
				const targetUnit = axis.targetUnits[varName] || nativeUnit;
				if (targetUnit) uniqueUnits.add(targetUnit);

				const points = dataInfo.x.map((x, i) => {
					const yVal = dataInfo.y[i];
					const converted = yVal !== null ? convertValue(yVal, nativeUnit, targetUnit) : null;
					return [x, converted];
				});

				const displayName = varDef ? varDef.name : varName;

				const chartType = axis.chartType || 'line';
				const fallbackColor = ['#f43f5e', '#f59e0b', '#10b981', '#06b6d4', '#6366f1'][idx % 5];
				const customColor = axis.variableColors?.[varName] || fallbackColor;
				const customStyle = axis.variableLineStyles?.[varName] || 'solid';
				const customMarker = axis.variableMarkers?.[varName] || 'circle';

				const itemName = `${displayName} [${targetUnit}]`;
				legendData.push(itemName);

				series.push({
					name: itemName,
					type: chartType === 'area' ? 'line' : chartType,
					showSymbol: chartType === 'scatter',
					symbol: chartType === 'scatter' ? customMarker : undefined,
					symbolSize: chartType === 'scatter' ? 5 : undefined,
					areaStyle: chartType === 'area' ? { opacity: 0.2 } : undefined,
					sampling: chartType === 'scatter' ? undefined : 'lttb',
					large: true,
					largeThreshold: 600,
					progressiveThreshold: 600,
					progressive: 400,
					hoverAnimation: false, // 최적화: 호버 시 점 커지는 애니메이션 끄기
					emphasis: { disabled: true }, // 최적화: 호버 시 다른 시리즈 투명해지는 효과 끄기
					data: points,
					connectNulls: false,
					lineStyle: {
						width: 1.5,
						type: customStyle
					},
					itemStyle: { color: customColor }
				});
			}
		});

		const textColor = '#1e293b';
		const mutedColor = '#64748b';
		const gridColor = '#e2e8f0';
		const tooltipBg = 'rgba(255, 255, 255, 0.9)';
		const tooltipBorder = '#cbd5e1';

		const unitStr = uniqueUnits.size === 1 ? ` [${Array.from(uniqueUnits)[0]}]` : '';

		function getFormattedTime(value: number) {
			const date = new Date(
				Date.UTC(viewerState.startYear, viewerState.startMonth - 1, viewerState.startDay, 0, 0, 0)
			);
			date.setUTCMinutes(value);
			const month = date.getUTCMonth() + 1;
			const day = date.getUTCDate();
			const hours = date.getUTCHours().toString().padStart(2, '0');
			const mins = date.getUTCMinutes().toString().padStart(2, '0');
			return { month, day, hours, mins };
		}

		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		const option: any = {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'axis',
				triggerOn: 'mousemove',
				throttle: 100, // 최적화: 너무 낮으면 호버시 버벅임 발생
				axisPointer: {
					type: 'line', // 'cross'보다 'line'이 연산량이 훨씬 적음
					animation: false,
					lineStyle: { color: mutedColor, width: 1, type: 'dashed' }
				},
				backgroundColor: tooltipBg,
				borderColor: tooltipBorder,
				enterable: false,
				confine: true,
				formatter: function (params: any) {
					if (!params || !params.length) return '';
					const valX = params[0].value[0];
					const dt = getFormattedTime(valX);
					let res = `<div style="margin-bottom: 6px; font-weight: 600;">${dt.month}m ${dt.day}d ${dt.hours}:${dt.mins}</div>`;
					params.forEach((p: any) => {
						const val = p.value[1];
						const formattedVal =
							val !== null && val !== undefined
								? val.toLocaleString('en-US', { maximumFractionDigits: 1 })
								: '-';
						// Skip background empty series if hovered
						if (p.seriesName === 'BackgroundDataZoom') return;
						res += `<div style="display: flex; justify-content: space-between; gap: 24px; align-items: center; margin-bottom: 2px;">
							<div style="display: flex; align-items: center;">${p.marker} <span style="font-size: 11px; margin-left: 4px;">${p.seriesName}</span></div>
							<span style="font-weight: 700;">${formattedVal}</span>
						</div>`;
					});
					return res;
				},
				textStyle: { color: textColor, fontSize: 12 }
			},
			legend: {
				show: true,
				data: legendData,
				textStyle: { color: mutedColor, fontWeight: 500 },
				type: 'plain',
				top: 5,
				width: '80%',
				height: 55,
				icon: 'circle',
				itemGap: 20
			},
			grid: {
				left: 90,
				right: '5%',
				bottom: 75,
				top: 85,
				containLabel: false
			},
			xAxis: {
				type: 'value',
				name: 'Time',
				nameLocation: 'end',
				nameGap: 10,
				nameTextStyle: { color: mutedColor, fontSize: 13 },
				scale: false,
				min: 0,
				max: viewerState.spanDays * 1440,
				axisLabel: {
					color: mutedColor,
					formatter: function (value: number) {
						// Create reference date starting from selected global Month
						const date = new Date(
							Date.UTC(
								viewerState.startYear,
								viewerState.startMonth - 1,
								viewerState.startDay,
								0,
								0,
								0
							)
						);
						date.setUTCMinutes(value);

						const month = date.getUTCMonth() + 1;
						const day = date.getUTCDate();
						const hours = date.getUTCHours().toString().padStart(2, '0');
						const mins = date.getUTCMinutes().toString().padStart(2, '0');

						const minDay = axis.xmin ?? 0;
						const maxDay = axis.xmax ?? viewerState.spanDays;
						const spanDays = maxDay - minDay;

						if (spanDays > 7.1) {
							return `${month}/${day}`;
						} else {
							return `${month}/${day} ${hours}:${mins}`;
						}
					}
				},
				axisPointer: {
					label: {
						formatter: function (params: any) {
							const dt = getFormattedTime(params.value);
							return `${dt.month}m ${dt.day}d ${dt.hours}:${dt.mins}`;
						}
					}
				},
				axisLine: { onZero: false },
				axisTick: { show: true },
				splitLine: { show: true, lineStyle: { color: gridColor, type: 'dashed' } }
			},
			yAxis: {
				type: 'value',
				name: axis.customYLabel || `Value${unitStr}`,
				triggerEvent: true,
				nameLocation: 'middle',
				nameGap: 75,
				nameTextStyle: { color: mutedColor, fontSize: 13 },
				min: axis.ymin !== null ? axis.ymin : undefined,
				max: axis.ymax !== null ? axis.ymax : undefined,
				scale: true,
				axisLabel: {
					color: mutedColor,
					width: 80,
					align: 'right',
					overflow: 'truncate',
					formatter: function (value: number) {
						return value.toLocaleString('en-US', { maximumFractionDigits: 1 });
					}
				},
				axisTick: { show: true },
				splitLine: { show: true, lineStyle: { color: gridColor } }
			},
			dataZoom: [
				{
					type: 'inside',
					xAxisIndex: 0,
					startValue: axis.xmin !== null ? axis.xmin * viewerState.spanDays * 1440 : undefined,
					endValue: axis.xmax !== null ? axis.xmax * viewerState.spanDays * 1440 : undefined
				},
				{
					type: 'slider',
					xAxisIndex: 0,
					bottom: 20,
					height: 25,
					borderColor: 'transparent',
					textStyle: { color: mutedColor },
					fillerColor: 'rgba(99,102,241,0.1)',
					moveHandleSize: 0,
					startValue: axis.xmin !== null ? axis.xmin * viewerState.spanDays * 1440 : undefined,
					endValue: axis.xmax !== null ? axis.xmax * viewerState.spanDays * 1440 : undefined
				}
			],
			series
		};
		console.log('CHART UPDATE OPTION:', series);

		chartInstance.setOption(option, { replaceMerge: ['series'] });
	}

	onMount(() => {
		if (chartContainer) {
			chartInstance = echarts.init(chartContainer);

			chartInstance.on('datazoom', (params: any) => {
				clearTimeout(zoomTimeout);
				zoomTimeout = setTimeout(() => {
					const opt = chartInstance?.getOption() as any;
					if (!opt || !opt.dataZoom || opt.dataZoom.length === 0) return;

					let xStartMin = opt.dataZoom[0].startValue ?? opt.dataZoom[0].start;
					let xEndMin = opt.dataZoom[0].endValue ?? opt.dataZoom[0].end;

					if (xStartMin !== undefined && xEndMin !== undefined) {
						// Convert from minutes to 0–1 ratio
						const totalMinutes = viewerState.spanDays * 1440;
						let newMin = typeof xStartMin === 'number' ? xStartMin / totalMinutes : 0;
						let newMax = typeof xEndMin === 'number' ? xEndMin / totalMinutes : 1;

						const currentMin = axis.xmin ?? 0;
						const currentMax = axis.xmax ?? 1;
						// If user swept mouse more than 0.01 ratio differences
						if (Math.abs(currentMin - newMin) > 0.001 || Math.abs(currentMax - newMax) > 0.001) {
							viewerState.setAxisXBounds(axis.id, newMin, newMax);
							viewerState.fetchResults();
						}
					}
				}, 400);
			});

			chartInstance.on('click', (params: any) => {
				// Only activate when clicking directly on the Y-axis name label
				if (params.componentType === 'yAxis' && params.targetType === 'axisName') {
					const opt = chartInstance?.getOption() as any;
					const currentName = opt?.yAxis?.[0]?.name || '';
					editYLabelText = axis.customYLabel || currentName;
					editYLabelPos = { x: params.event.offsetX, y: params.event.offsetY };
					editingYLabel = true;
				}
			});

			isMounted = true;

			// Handle resize
			resizeObserver = new ResizeObserver(() => {
				chartInstance?.resize();
			});
			resizeObserver.observe(chartContainer);
		}

		return () => {
			if (resizeObserver) resizeObserver.disconnect();
			chartInstance?.dispose();
		};
	});

	async function generateExportBlob(type: 'png' | 'svg'): Promise<Blob> {
		const hiddenDiv = document.createElement('div');
		hiddenDiv.style.width = chartContainer.clientWidth + 'px';
		hiddenDiv.style.height = chartContainer.clientHeight + 'px';

		const isSvg = type === 'svg';
		const hiddenChart = echarts.init(hiddenDiv, undefined, { renderer: isSvg ? 'svg' : 'canvas' });

		const opt = chartInstance!.getOption() as any;
		opt.animation = false;
		opt.backgroundColor = isSvg ? 'transparent' : '#ffffff';

		if (opt.dataZoom) {
			opt.dataZoom = opt.dataZoom.filter((dz: any) => dz.type !== 'slider');
		}
		if (Array.isArray(opt.grid)) {
			opt.grid[0].bottom = 40;
		} else if (opt.grid) {
			opt.grid.bottom = 40;
		}

		hiddenChart.setOption(opt);

		let blob: Blob;
		if (isSvg) {
			const svgStr = hiddenChart.renderToSVGString();
			blob = new Blob([svgStr], { type: 'image/svg+xml' });
		} else {
			const dataUrl = hiddenChart.getDataURL({
				type: 'png',
				pixelRatio: 300 / 72,
				backgroundColor: '#fff'
			});
			const res = await fetch(dataUrl);
			blob = await res.blob();
		}

		hiddenChart.dispose();
		return blob;
	}

	async function exportChart(type: 'png' | 'svg') {
		if (!chartInstance) return;
		const name = `chart_export.${type}`;
		try {
			const handle = await (window as any).showSaveFilePicker({
				suggestedName: name,
				types: [
					{
						description: `${type.toUpperCase()} Image`,
						accept: { [`image/${type}`]: [`.${type}`] }
					}
				]
			});
			const writable = await handle.createWritable();
			const blob = await generateExportBlob(type);
			await writable.write(blob);
			await writable.close();
		} catch (err: any) {
			if (err.name !== 'AbortError') {
				if (err.message && err.message.includes('not a function')) {
					fallbackDownload(type, name);
				} else {
					console.error('Export failed:', err);
				}
			}
		}
	}

	async function fallbackDownload(type: 'png' | 'svg', filename: string) {
		const blob = await generateExportBlob(type);
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	async function copyChart() {
		try {
			isCopying = true;
			const blob = await generateExportBlob('png');
			const ClipboardItem = (window as any).ClipboardItem;
			if (!ClipboardItem) {
				throw new Error('ClipboardItem not supported');
			}
			const item = new ClipboardItem({ 'image/png': blob });
			await navigator.clipboard.write([item]);
			setTimeout(() => {
				isCopying = false;
			}, 1500);
		} catch (err) {
			console.error('Failed to copy image: ', err);
			alert('Clipboard copy failed. Your browser might not support this feature.');
			isCopying = false;
		}
	}
</script>

<div class="chart-wrapper">
	{#if axis.variables.length === 0}
		<div class="empty-state">
			<span class="empty-icon">📊</span>
			<p>Select variables to generate a chart</p>
		</div>
	{/if}
	<div
		bind:this={chartContainer}
		class="chart-container"
		style="visibility: {axis.variables.length > 0 ? 'visible' : 'hidden'}"
	></div>
	{#if axis.variables.length > 0}
		<div class="export-buttons">
			<button
				class="export-btn icon-btn"
				onclick={copyChart}
				title="Copy as PNG to Clipboard"
				aria-label="Copy to Clipboard"
			>
				{#if isCopying}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="14"
						height="14"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						style="color: #10b981;"><polyline points="20 6 9 17 4 12"></polyline></svg
					>
				{:else}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="14"
						height="14"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path
							d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
						></path></svg
					>
				{/if}
			</button>
			<button class="export-btn" onclick={() => exportChart('png')} title="Save as PNG (300 DPI)"
				>PNG</button
			>
			<button class="export-btn" onclick={() => exportChart('svg')} title="Save as SVG">SVG</button>
		</div>
	{/if}

	{#if editingYLabel}
		<input
			type="text"
			class="inline-ylabel-input"
			bind:value={editYLabelText}
			style="left: {editYLabelPos.x}px; top: {editYLabelPos.y}px;"
			onblur={() => {
				viewerState.setAxisCustomYLabel(axis.id, editYLabelText);
				editingYLabel = false;
				updateChart();
			}}
			onkeydown={(e) => {
				if (e.key === 'Enter') {
					viewerState.setAxisCustomYLabel(axis.id, editYLabelText);
					editingYLabel = false;
					updateChart();
				} else if (e.key === 'Escape') {
					editingYLabel = false;
				}
			}}
			use:focusInput
		/>
	{/if}
</div>

<style>
	.chart-wrapper {
		position: relative;
		width: 100%;
		height: 480px;
		border-radius: 12px;
		overflow: hidden;
		transition: all 0.3s;
		display: flex;
		flex-direction: column;
		background: #f8fafc;
		border: 1px solid var(--border-light);
	}

	.chart-container {
		width: 100%;
		flex: 1;
		min-height: 0;
	}
	.empty-state {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		color: var(--text-muted-light);
	}
	.empty-icon {
		font-size: 32px;
		opacity: 0.6;
		filter: grayscale(1);
	}
	.empty-state p {
		font-size: 14px;
		font-weight: 500;
		margin: 0;
	}
	.export-buttons {
		position: absolute;
		top: 12px;
		right: 12px;
		display: flex;
		gap: 6px;
		z-index: 10;
	}
	.export-btn {
		background: white;
		border: 1px solid var(--border-light);
		border-radius: 6px;
		padding: 4px 8px;
		font-size: 11px;
		font-weight: 600;
		color: var(--text-muted-light);
		cursor: pointer;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.export-btn:hover {
		background: var(--bg-hover);
		color: var(--primary-color, #6366f1);
		border-color: var(--primary-color, #6366f1);
	}
	.inline-ylabel-input {
		position: absolute;
		transform: translate(-50%, -50%) rotate(-90deg);
		z-index: 20;
		background: white;
		border: 1px solid var(--primary-color, #6366f1);
		border-radius: 4px;
		padding: 4px 8px;
		font-size: 13px;
		color: var(--text-color, #1e293b);
		box-shadow:
			0 4px 6px -1px rgba(0, 0, 0, 0.1),
			0 2px 4px -1px rgba(0, 0, 0, 0.06);
		outline: none;
		min-width: 150px;
		text-align: center;
	}
</style>
