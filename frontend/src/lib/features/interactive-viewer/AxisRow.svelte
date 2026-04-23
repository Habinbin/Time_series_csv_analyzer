<script lang="ts">
	import type { ChartAxis } from './state.svelte';
	import ChartControls from './components/ChartControls.svelte';
	import SingleChart from './components/SingleChart.svelte';

	let { axis, index }: { axis: ChartAxis, index: number } = $props();
</script>

<div class="axis-row">
	<div class="axis-config">
		<ChartControls {axis} {index} />
	</div>
	<div class="axis-plot">
		<SingleChart {axis} {index} />
	</div>
</div>

<style>
	.axis-row {
		display: flex;
		flex-direction: row;
		background-color: #ffffff;
		border-radius: 12px;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
		border: 1px solid #e2e8f0;
		margin: 16px 32px;
		overflow: visible;
		align-items: stretch;
	}
	.axis-config {
		width: 340px;
		flex-shrink: 0;
		border-right: 1px solid #f1f5f9;
		background-color: transparent;
	}
	.axis-plot {
		flex: 1;
		min-width: 0; /* Important for flex items containing ECharts */
		padding: 24px;
	}
</style>
