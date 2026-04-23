<script lang="ts">
	import InteractiveViewer from '$lib/features/interactive-viewer/InteractiveViewer.svelte';
	import { Activity } from 'lucide-svelte';
</script>

<svelte:head>
	<title>Time Series Data Visualizer</title>
</svelte:head>

<main>
	<header class="app-header">
		<div class="logo">
			<Activity color="#4f46e5" size={28} strokeWidth={2.5} class="brand-icon" />
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
