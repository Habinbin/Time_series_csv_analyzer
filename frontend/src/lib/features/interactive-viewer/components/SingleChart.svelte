<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as echarts from 'echarts';
	import type { ChartAxis } from '../state.svelte';
	import { viewerState } from '../state.svelte';
	import { convertValue } from '../units';

	let { axis, index }: { axis: ChartAxis; index: number } = $props();

	let chartContainer: HTMLDivElement;
	let chartInstance: echarts.ECharts | null = null;
	let resizeObserver: ResizeObserver | null = null;
	let zoomTimeout: ReturnType<typeof setTimeout> | undefined;

	// Watch data and bounds to update chart
	$effect(() => {
		if (chartInstance && !viewerState.loading) {
			updateChart();
		}
	});

	// Re-init chart when container is ready
	$effect(() => {
		if (chartContainer) {
			if (chartInstance) {
				chartInstance.dispose();
			}
			chartInstance = echarts.init(chartContainer);

			chartInstance.on('datazoom', (params: any) => {
				clearTimeout(zoomTimeout);
				zoomTimeout = setTimeout(() => {
					const opt = chartInstance?.getOption() as any;
					if (!opt || !opt.dataZoom || opt.dataZoom.length === 0) return;

					let xStartMin = opt.dataZoom[0].startValue ?? opt.dataZoom[0].start;
					let xEndMin = opt.dataZoom[0].endValue ?? opt.dataZoom[0].end;

					if (xStartMin !== undefined && xEndMin !== undefined) {
						let newMin = typeof xStartMin === 'number' ? xStartMin / 1440 : 0;
						let newMax = typeof xEndMin === 'number' ? xEndMin / 1440 : viewerState.spanDays;

						const currentMin = axis.xmin || 0;
						const currentMax = axis.xmax || viewerState.spanDays;
						// If user swept mouse more than 1 min differences
						if (Math.abs(currentMin - newMin) > 0.01 || Math.abs(currentMax - newMax) > 0.01) {
							viewerState.setAxisXBounds(axis.id, newMin, newMax);
							viewerState.fetchResults();
						}
					}
				}, 400);
			});

			updateChart();
		}
	});

	function updateChart() {
		if (!chartInstance) return;

		const series: any[] = [];
		const legendData: string[] = [];
		const uniqueUnits = new Set<string>();

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
					data: points,
					showSymbol: false,
					tooltip: { show: false },
					lineStyle: { opacity: 0 },
					itemStyle: { opacity: 0 },
					animation: false,
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
					sampling: 'none',
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
				Date.UTC(2023, viewerState.startMonth - 1, viewerState.startDay, 0, 0, 0)
			);
			date.setUTCMinutes(value);
			const month = date.getUTCMonth() + 1;
			const day = date.getUTCDate();
			const hours = date.getUTCHours().toString().padStart(2, '0');
			const mins = date.getUTCMinutes().toString().padStart(2, '0');
			return { month, day, hours, mins };
		}

		const option: echarts.EChartsOption = {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'axis',
				axisPointer: { type: 'cross' },
				backgroundColor: tooltipBg,
				borderColor: tooltipBorder,
				formatter: function (params: any) {
					if (!params || !params.length) return '';
					const valX = params[0].value[0];
					const dt = getFormattedTime(valX);
					let res = `<div style="margin-bottom: 6px; font-weight: 600;">${dt.month}m ${dt.day}d ${dt.hours}:${dt.mins}</div>`;
					params.forEach((p: any) => {
						const val = p.value[1];
						const formattedVal =
							val !== null && val !== undefined
								? val.toLocaleString('en-US', { maximumFractionDigits: 3 })
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
				type: 'scroll',
				top: 5,
				icon: 'circle',
				itemGap: 20
			},
			grid: {
				left: 90,
				right: '5%',
				bottom: 75,
				top: '15%',
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
							Date.UTC(2023, viewerState.startMonth - 1, viewerState.startDay, 0, 0, 0)
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
				axisTick: { show: true },
				splitLine: { show: true, lineStyle: { color: gridColor, type: 'dashed' } }
			},
			yAxis: {
				type: 'value',
				name: `Value${unitStr}`,
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
						return value.toLocaleString('en-US', { maximumFractionDigits: 3 });
					}
				},
				axisTick: { show: true },
				splitLine: { show: true, lineStyle: { color: gridColor } }
			},
			dataZoom: [
				{
					type: 'inside',
					xAxisIndex: 0,
					startValue: axis.xmin !== null ? axis.xmin * 1440 : undefined,
					endValue: axis.xmax !== null ? axis.xmax * 1440 : undefined
				},
				{
					type: 'slider',
					xAxisIndex: 0,
					bottom: 20,
					height: 25,
					borderColor: 'transparent',
					textStyle: { color: mutedColor },
					fillerColor: 'rgba(99,102,241,0.1)',
					startValue: axis.xmin !== null ? axis.xmin * 1440 : undefined,
					endValue: axis.xmax !== null ? axis.xmax * 1440 : undefined
				}
			],
			series
		};

		chartInstance.setOption(option, true);
	}

	onMount(() => {
		// chartInstance is managed by the $effect block for theme
		// Handle resize
		resizeObserver = new ResizeObserver(() => {
			chartInstance?.resize();
		});
		resizeObserver.observe(chartContainer);

		return () => {
			if (resizeObserver) resizeObserver.disconnect();
			chartInstance?.dispose();
		};
	});
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
</style>
