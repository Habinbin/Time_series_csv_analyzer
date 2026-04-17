<script lang="ts">
	import InteractiveViewer from '$lib/features/interactive-viewer/InteractiveViewer.svelte';
</script>

<svelte:head>
	<title>Time Series Data Visualizer</title>
</svelte:head>

<main>
	<header class="app-header">
		<div class="logo">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="brand-icon">
				<path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#3b82f6" />
				<path
					d="M2 17L12 22L22 17"
					stroke="#3b82f6"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
				<path
					d="M2 12L12 17L22 12"
					stroke="#3b82f6"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
			<h1>Time Series Data Visualizer</h1>
		</div>
	</header>

	<InteractiveViewer />
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		background: #f8fafc;
		color: #0f172a;
		font-family: 'Inter', system-ui, sans-serif;
	}

	.app-header {
		height: 4rem;
		background: #ffffff;
		border-bottom: 1px solid #e2e8f0;
		display: flex;
		align-items: center;
		padding: 0 2rem;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.logo h1 {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		letter-spacing: -0.02em;
		color: #0f172a;
	}
</style>
