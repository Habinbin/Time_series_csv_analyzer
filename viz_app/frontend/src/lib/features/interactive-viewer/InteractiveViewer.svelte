<script lang="ts">
	import { onMount } from 'svelte';
	import { viewerState } from './state.svelte';
	import AxisRow from './AxisRow.svelte';

	onMount(() => {
		viewerState.fetchVariables();
	});

	// No theme effect needed as we force Light Mode

	let dragActive = $state(false);

	function onDragOver(e: DragEvent) {
		e.preventDefault();
		dragActive = true;
	}

	function onDragLeave(e: DragEvent) {
		e.preventDefault();
		const related = e.relatedTarget as HTMLElement | null;
		// Prevents flickering when dragging over child elements
		if (!related || !related.closest('.viewer-container')) {
			dragActive = false;
		}
	}

	async function onDrop(e: DragEvent) {
		e.preventDefault();
		dragActive = false;
		
		const file = e.dataTransfer?.files[0];
		if (file) {
			if (file.name.toLowerCase().endsWith('.csv')) {
				await viewerState.uploadCsv(file);
			} else {
				alert('Please drop a valid .csv file');
			}
		}
	}
</script>

<div 
	class="viewer-container"
	role="region"
	aria-label="Drag and Drop zone"
	ondragover={onDragOver}
	ondragleave={onDragLeave}
	ondrop={onDrop}
>
	{#if dragActive}
		<div class="drag-overlay panel-light">
			<div class="drag-message">
				<div class="icon">📄</div>
				<h2>Replace Simulation Datastore</h2>
				<p>Drop your 1-yr Simulation CSV here to analyze</p>
			</div>
		</div>
	{/if}

	{#if viewerState.loading}
		<div class="global-loading-overlay">
			<div class="spinner"></div>
			<p>Loading data...</p>
		</div>
	{/if}

	<div class="row-header">
		<div class="drag-message-inline">
			<p class="subtitle">Drop a new CSV anywhere to hot-swap datastore</p>
		</div>
		<div class="header-controls">
			<label class="timestep-input">
				<span>Timestep (min):</span>
				<input type="number" bind:value={viewerState.timestep} min="1" step="1" />
			</label>
		</div>
	</div>

	<div class="rows-container">
		{#if viewerState.axes.length === 0}
			<div class="empty-state">
				<p>No axes configured. Add an axis to begin visualization.</p>
			</div>
		{/if}
		{#each viewerState.axes as ax, i (ax.id)}
			<AxisRow axis={ax} index={i} />
		{/each}

		<div class="add-axis-footer">
			<button class="btn-add-large" onclick={() => viewerState.addAxis()}>+ Add Axis</button>
		</div>
	</div>
</div>

<style>
	:global(:root) {
		/* Level Colors */
		--bg-level-0-dark: #020617; /* slate-950 */
		--bg-level-1-dark: #0f172a; /* slate-900 */
		--bg-level-2-dark: #1e293b; /* slate-800 */
		--border-dark: rgba(255, 255, 255, 0.03); /* almost transparent */
		--text-dark: #f8fafc;
		--text-muted-dark: #94a3b8;
		--shadow-dark: none;

		--bg-level-0-light: #f8fafc; /* slate-50 */
		--bg-level-1-light: #ffffff; /* white */
		--bg-level-2-light: #f1f5f9; /* slate-100 */
		--border-light: rgba(0, 0, 0, 0.04);
		--text-light: #0f172a;
		--text-muted-light: #64748b;
		--shadow-light: 0 4px 6px -1px rgba(0,0,0,0.05);

		/* Typography */
		--font-base: 'Inter', system-ui, sans-serif;
		--text-base: 14px;
		--text-h1: 24px;
		--text-h2: 18px;
		--text-sm: 12px;
		--leading-base: 1.5;
		--leading-h: 1.2;

		/* Accent */
		--accent-primary: #5c83c4; /* Soft muted blue */
		--accent-hover: #4a6fa8;
		--danger-color: #ef4444;
	}

	:global(body) {
		margin: 0;
		font-family: var(--font-base);
		font-size: var(--text-base);
		line-height: var(--leading-base);
		background-color: var(--bg-level-0-light);
		color: var(--text-light);
	}

	.viewer-container {
		display: flex;
		flex-direction: column;
		min-height: calc(100vh - 4rem);
		position: relative;
	}
	
	.drag-overlay {
		position: absolute;
		top: 16px; left: 16px; right: 16px; bottom: 16px;
		background: rgba(243, 244, 246, 0.85);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		z-index: 100;
		border: 2px dashed var(--accent-primary);
		border-radius: 16px;
		display: flex;
		align-items: center;
		justify-content: center;
		animation: fade-in 0.2s ease-out;
	}
	
	.drag-message {
		text-align: center;
		pointer-events: none; /* So the drop targets the overlay seamlessly */
	}
	.drag-message .icon {
		font-size: 48px;
		margin-bottom: 16px;
		animation: bounce 1s infinite alternate;
	}
	.drag-message h2 {
		margin: 0 0 8px 0;
		color: var(--accent-primary);
		font-size: var(--text-h1);
	}
	.drag-message p {
		margin: 0;
		color: var(--text-muted-light);
	}
	
	@keyframes bounce {
		0% { transform: translateY(0); }
		100% { transform: translateY(-10px); }
	}
	@keyframes fade-in {
		0% { opacity: 0; }
		100% { opacity: 1; }
	}
	
	.row-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		height: 64px;
		padding: 0 32px;
		border-bottom: 1px solid #e2e8f0;
		background: #ffffff;
	}
	.drag-message-inline p {
		margin: 0;
		color: #0f172a;
		font-weight: 600;
		font-size: var(--text-base);
	}
	.add-axis-footer {
		display: flex;
		justify-content: center;
		padding: 24px;
	}
	.btn-add-large {
		background: transparent;
		color: var(--accent-primary);
		border: 2px dashed var(--accent-primary);
		border-radius: 8px;
		padding: 12px 32px;
		font-size: var(--text-base);
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn-add-large:hover {
		background: rgba(92, 131, 196, 0.1);
	}
	.header-controls {
		display: flex;
		align-items: center;
		gap: 16px;
	}
	.timestep-input {
		display: flex;
		align-items: center;
		gap: 8px;
		color: #475569;
		font-weight: 500;
		font-size: var(--text-sm);
	}
	.timestep-input input {
		width: 60px;
		padding: 6px 8px;
		border: 1px solid #cbd5e1;
		border-radius: 6px;
		font-family: inherit;
		font-size: var(--text-sm);
		text-align: center;
	}
	.timestep-input input:focus {
		outline: none;
		border-color: var(--accent-primary);
		box-shadow: 0 0 0 2px rgba(92, 131, 196, 0.2);
	}
	.rows-container {
		display: flex;
		flex-direction: column;
		flex: 1;
	}
	.empty-state {
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-muted-light);
		min-height: 400px;
		margin: 32px;
		border: 1px dashed var(--border-light);
		border-radius: 12px;
	}
	
	/* Global Loading Overlay */
	.global-loading-overlay {
		position: fixed;
		top: 0; left: 0; right: 0; bottom: 0;
		background: rgba(255, 255, 255, 0.7);
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		z-index: 9999;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		color: var(--accent-primary);
	}
	.spinner {
		width: 48px;
		height: 48px;
		border: 4px solid rgba(92, 131, 196, 0.2);
		border-top-color: var(--accent-primary);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 16px;
	}
	.global-loading-overlay p {
		font-size: var(--text-h1);
		font-weight: 600;
		margin: 0;
	}
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
