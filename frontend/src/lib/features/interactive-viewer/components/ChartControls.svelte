<script lang="ts">
	import type { ChartAxis } from '../state.svelte';
	import { viewerState } from '../state.svelte';
	import { getAvailableConversions } from '../units';

	let { axis, index }: { axis: ChartAxis; index: number } = $props();

	// Variables computed from global state
	let vars = $derived(viewerState.availableVariables);
	let searchQuery = $state('');
	let showDropdown = $state(false);
	let filteredVars = $derived(
		searchQuery
			? vars.filter(
					(v) =>
						v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
						v.raw_col.toLowerCase().includes(searchQuery.toLowerCase())
				)
			: vars
	);

	function dayToDateStr(dayValue: number | null): string {
		if (dayValue === null || isNaN(dayValue)) return '';
		const date = new Date(
			Date.UTC(viewerState.startYear, viewerState.startMonth - 1, viewerState.startDay, 0, 0, 0)
		);
		date.setUTCMinutes(dayValue * 1440);
		return date.toISOString().split('T')[0];
	}

	function dateStrToDay(dateStr: string): string | null {
		if (!dateStr) return null;
		const [year, month, day] = dateStr.split('-');
		const targetDate = new Date(
			Date.UTC(parseInt(year), parseInt(month) - 1, parseInt(day), 0, 0, 0)
		);
		const baseDate = new Date(
			Date.UTC(viewerState.startYear, viewerState.startMonth - 1, viewerState.startDay, 0, 0, 0)
		);
		return ((targetDate.getTime() - baseDate.getTime()) / (1000 * 60 * 60 * 24)).toString();
	}

	function selectVar(raw_col: string) {
		if (!axis.variables.includes(raw_col)) {
			viewerState.setAxisVariables(axis.id, [...axis.variables, raw_col]);
		}
		searchQuery = '';
		showDropdown = false;
	}

	function removeVariable(v: string) {
		viewerState.setAxisVariables(
			axis.id,
			axis.variables.filter((x) => x !== v)
		);
	}
</script>

<div class="control-panel">
	<div class="header">
		<div class="header-main">
			<span class="axis-badge">{index + 1}</span>
			<div class="chart-type-segment" role="group">
				{#each ['line', 'scatter', 'area'] as type}
					<button
						class="btn-segment"
						class:active={axis.chartType === type || (!axis.chartType && type === 'line')}
						onclick={() =>
							viewerState.setAxisChartType(axis.id, type as 'line' | 'scatter' | 'area')}
					>
						{type.charAt(0).toUpperCase() + type.slice(1)}
					</button>
				{/each}
			</div>
		</div>
		<button class="btn-danger" onclick={() => viewerState.removeAxis(axis.id)}> Remove </button>
	</div>

	<div class="field relative-field">
		<label for="var-add-{axis.id}">Add variable</label>
		<input
			type="text"
			id="var-add-{axis.id}"
			bind:value={searchQuery}
			placeholder="Search and select..."
			class="var-select-single"
			onfocus={() => (showDropdown = true)}
			onblur={() => setTimeout(() => (showDropdown = false), 200)}
		/>
		{#if showDropdown}
			<ul class="custom-dropdown">
				{#each filteredVars as v}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
					<li class="dropdown-item" onmousedown={() => selectVar(v.raw_col)}>
						<span class="dropdown-item-name" title={v.name}>{v.name}</span>
						{#if v.unit}
							<span class="dropdown-item-unit">[{v.unit}]</span>
						{/if}
					</li>
				{/each}
				{#if filteredVars.length === 0}
					<li class="dropdown-item-empty">No matching variables</li>
				{/if}
			</ul>
		{/if}
	</div>

	<div class="selected-vars-list">
		{#each axis.variables as v}
			{@const varDef = viewerState.availableVariables.find((x) => x.raw_col === v)}
			{@const nativeUnit = varDef?.unit || ''}
			{@const sourceUnit = axis.sourceUnits?.[v] || nativeUnit}
			{@const targetUnit = axis.targetUnits?.[v] || sourceUnit}
			{@const available = getAvailableConversions(sourceUnit)}

			<div class="var-row">
				<div class="var-main">
					<span
						class="var-name"
						title={varDef ? varDef.name.replace(/Consumption/gi, 'Energy Use') : v}
						>{varDef ? varDef.name.replace(/Consumption/gi, 'Energy Use') : v}</span
					>
				</div>

				<!-- Color Picker & Style -->
				<div class="var-toggles">
					<!-- Color Cycle Button -->
					<button
						class="color-circle"
						style="background: {axis.variableColors?.[v]}"
						onclick={() => viewerState.cycleAxisVariableColor(axis.id, v)}
						title="Change line color"
					></button>

					{#if axis.chartType === 'line'}
						<!-- Line Style Toggle -->
						{@const lineLabel = { solid: '-', dashed: '--', dashdot: '-.', dotted: ':' }[
							axis.variableLineStyles?.[v] || 'solid'
						]}
						<button
							class="cycle-style-btn"
							onclick={() => viewerState.cycleAxisVariableLineStyle(axis.id, v)}
							title="Change line style">{lineLabel}</button
						>
					{/if}

					{#if axis.chartType === 'scatter'}
						<!-- Marker Style Toggle -->
						{@const markerLabel = { circle: '●', rect: '■', triangle: '▲', diamond: '◆' }[
							axis.variableMarkers?.[v] || 'circle'
						]}
						<button
							class="cycle-style-btn"
							onclick={() => viewerState.cycleAxisVariableMarker(axis.id, v)}
							title="Cycle marker style">{markerLabel}</button
						>
					{/if}
				</div>

				<!-- Physical Unit -->
				<div class="var-unit">
					{#if available.length > 0}
						<select
							class="unit-select unit-target"
							value={targetUnit}
							onchange={(e) => {
								viewerState.setAxisVariableSourceUnit(axis.id, v, sourceUnit); // Ensure source is locked
								viewerState.setAxisVariableUnit(axis.id, v, e.currentTarget.value);
							}}
						>
							{#each available as u}
								<option value={u}>{u}</option>
							{/each}
						</select>
					{:else if nativeUnit}
						<span class="unit-badge" title={nativeUnit}>[{nativeUnit}]</span>
					{/if}
				</div>

				<!-- Remove Action -->
				<button class="chip-remove" title="Remove variable" onclick={() => removeVariable(v)}
					>×</button
				>
			</div>
		{/each}
	</div>

	<div class="bounds-container">
		<div class="bounds-header">
			<span>X-axis range (days)</span>
		</div>
		<div class="bounds-row">
			<div class="field">
				<label for="xmin-{axis.id}">Start day</label>
				<input
					id="xmin-{axis.id}"
					type="date"
					lang="en"
					value={dayToDateStr(axis.xmin)}
					onchange={(e) => {
						const val = (e.currentTarget as HTMLInputElement).value;
						const parsed = dateStrToDay(val);
						viewerState.setAxisXBounds(axis.id, parsed ? parseFloat(parsed) : null, axis.xmax);
						viewerState.fetchResults();
					}}
				/>
			</div>
			<div class="field">
				<label for="xmax-{axis.id}">End day</label>
				<input
					id="xmax-{axis.id}"
					type="date"
					lang="en"
					value={dayToDateStr(axis.xmax)}
					onchange={(e) => {
						const val = (e.currentTarget as HTMLInputElement).value;
						const parsed = dateStrToDay(val);
						viewerState.setAxisXBounds(axis.id, axis.xmin, parsed ? parseFloat(parsed) : null);
						viewerState.fetchResults();
					}}
				/>
			</div>
		</div>
	</div>

	<div class="bounds-container">
		<div class="bounds-header">
			<span>Y-axis scale</span>
			<label class="toggle-switch">
				<input
					type="checkbox"
					checked={axis.autoScale}
					onchange={(e) =>
						viewerState.setAxisAutoScale(axis.id, (e.currentTarget as HTMLInputElement).checked)}
				/>
				<span class="slider"></span>
				<span class="toggle-label">Auto</span>
			</label>
		</div>
		<div class="bounds-row" class:disabled={axis.autoScale}>
			<div class="field">
				<label for="ymin-{axis.id}">Min y</label>
				<input
					id="ymin-{axis.id}"
					type="number"
					step="any"
					disabled={axis.autoScale}
					value={axis.ymin ?? ''}
					onchange={(e) => {
						const val = (e.currentTarget as HTMLInputElement).value;
						viewerState.setAxisBounds(axis.id, val ? parseFloat(val) : null, axis.ymax);
					}}
					placeholder={axis.autoScale ? 'Auto' : 'Min'}
				/>
			</div>
			<div class="field">
				<label for="ymax-{axis.id}">Max y</label>
				<input
					id="ymax-{axis.id}"
					type="number"
					step="any"
					disabled={axis.autoScale}
					value={axis.ymax ?? ''}
					onchange={(e) => {
						const val = (e.currentTarget as HTMLInputElement).value;
						viewerState.setAxisBounds(axis.id, axis.ymin, val ? parseFloat(val) : null);
					}}
					placeholder={axis.autoScale ? 'Auto' : 'Max'}
				/>
			</div>
		</div>
	</div>
</div>

<style>
	.control-panel {
		padding: 24px;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}
	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: -16px; /* offset some gap for tight header */
	}
	.header-main {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.axis-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		background: rgba(99, 102, 241, 0.15);
		color: #4f46e5;
		border-radius: 50%;
		font-size: var(--text-sm);
		font-weight: 700;
		flex-shrink: 0;
	}
	.chart-type-segment {
		display: inline-flex;
		border-radius: 6px;
		background: #f1f5f9;
		border: 1px solid #e2e8f0;
		overflow: hidden;
		padding: 2px;
		gap: 2px;
	}
	.btn-segment {
		background: transparent;
		color: #475569;
		border: none;
		border-radius: 4px;
		padding: 4px 12px;
		font-size: 12px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn-segment:hover {
		background: #e2e8f0;
	}
	.btn-segment.active {
		background: #4f46e5;
		color: white;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
	}
	.btn-danger {
		background: transparent;
		color: var(--text-muted-light);
		border: 1px solid var(--border-light);
		border-radius: 6px;
		padding: 4px 10px;
		cursor: pointer;
		font-size: 12px;
		font-weight: 500;
		transition: all 0.2s;
	}
	.btn-danger:hover {
		color: var(--danger-color);
		border-color: rgba(239, 68, 68, 0.3);
		background: rgba(239, 68, 68, 0.05);
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.relative-field {
		position: relative;
	}
	label {
		font-size: var(--text-sm);
		font-weight: 500;
		letter-spacing: 0.01em;
		opacity: 0.8;
	}
	.var-select-single {
		background: #ffffff;
		border: 1px solid #cbd5e1;
		color: #334155;
		border-radius: 8px;
		padding: 8px 12px;
		font-size: var(--text-sm);
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
	}
	.custom-dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		z-index: 50;
		max-height: 250px;
		overflow-y: auto;
		background: #ffffff;
		border: 1px solid #cbd5e1;
		border-radius: 8px;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
		margin: 4px 0 0 0;
		padding: 0;
		list-style: none;
	}
	.dropdown-item {
		padding: 8px 12px;
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 8px;
		border-bottom: 1px solid #f1f5f9;
		transition: background-color 0.2s;
	}
	.dropdown-item:last-child {
		border-bottom: none;
	}
	.dropdown-item:hover {
		background-color: #f8fafc;
	}
	.dropdown-item-name {
		font-size: 13px;
		color: #334155;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.dropdown-item-unit {
		font-size: 11px;
		color: #64748b;
		flex-shrink: 0;
	}
	.dropdown-item-empty {
		padding: 12px;
		font-size: 13px;
		color: #94a3b8;
		text-align: center;
	}
	.selected-vars-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
		margin-top: -16px; /* pull closer to select */
	}
	.var-row {
		background: #ffffff;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		padding: 8px 6px 8px 12px;
		display: grid;
		grid-template-columns: 1fr 50px 60px 24px;
		align-items: center;
		gap: 8px;
	}
	.var-main {
		display: flex;
		align-items: center;
		min-width: 0;
	}
	.var-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		font-size: var(--text-sm);
		font-weight: 500;
	}
	.var-toggles {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		border-right: 1px solid var(--border-light);
		padding-right: 8px;
	}
	.var-unit {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 0;
	}
	.unit-select {
		background: #ffffff;
		border: 1px solid #e2e8f0;
		color: #334155;
		border-radius: 4px;
		padding: 2px 4px;
		font-size: 11px;
		cursor: pointer;
		width: 100%;
		text-overflow: ellipsis;
	}
	.unit-badge {
		background: var(--bg-level-1-light);
		border: 1px solid var(--border-light);
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 11px;
		color: var(--text-muted-light);
		width: 100%;
		text-align: center;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.chip-remove {
		background: none;
		border: none;
		color: var(--text-muted-light);
		cursor: pointer;
		font-size: 16px;
		line-height: 1;
		padding: 2px 0;
		opacity: 0;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.var-row:hover .chip-remove {
		opacity: 0.5;
	}
	.chip-remove:hover {
		opacity: 1 !important;
		color: white !important;
		background: var(--danger-color) !important;
		border-radius: 4px;
	}
	.bounds-container {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.bounds-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		font-size: 13px;
		font-weight: 500;
		color: var(--text-muted-light);
	}

	.bounds-row {
		display: flex;
		gap: 16px;
		align-items: flex-end;
		transition: opacity 0.3s;
	}
	.bounds-row.disabled {
		opacity: 0.4;
		pointer-events: none;
	}

	.bounds-row input {
		width: 100%;
		background: var(--bg-level-1-light);
		border: 1px solid var(--border-light);
		color: inherit;
		border-radius: 6px;
		padding: 6px 10px;
		font-size: var(--text-base);
	}

	/* Toggle Switch */
	.toggle-switch {
		position: relative;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
	}
	.toggle-switch input {
		display: none;
	}
	.slider {
		display: inline-block;
		width: 32px;
		height: 18px;
		background-color: #cbd5e1;
		border-radius: 34px;
		position: relative;
		transition: background-color 0.2s;
	}
	.slider:before {
		content: '';
		position: absolute;
		height: 12px;
		width: 12px;
		left: 3px;
		bottom: 3px;
		background-color: white;
		border-radius: 50%;
		transition: transform 0.2s;
	}
	.toggle-switch input:checked + .slider {
		background-color: var(--accent-primary);
	}
	.toggle-switch input:checked + .slider:before {
		transform: translateX(14px);
	}
	.toggle-label {
		font-size: 12px;
		font-weight: 600;
	}

	/* Removed custom-toggles since we use var-toggles now */
	.color-circle {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.2);
		cursor: pointer;
		padding: 0;
		transition: transform 0.1s;
	}
	.color-circle:hover {
		transform: scale(1.1);
	}
	.cycle-style-btn {
		min-width: 22px;
		height: 22px;
		background: var(--bg-level-2-light);
		border: 1px solid var(--border-light);
		border-radius: 4px;
		font-size: 11px;
		font-weight: bold;
		color: var(--text-light);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 4px;
	}
	.cycle-style-btn:hover {
		background: #e2e8f0;
	}
</style>
