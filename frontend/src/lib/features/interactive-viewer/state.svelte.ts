import { api } from '../../api/client';

export type VariableInfo = {
	name: string;
	unit: string;
	raw_col: string;
};

export type ChartAxis = {
	id: string;
	variables: string[];
	sourceUnits: Record<string, string>; // Maps `raw_col` to its selected source unit 
	targetUnits: Record<string, string>; // Maps `raw_col` to its selected target unit
	variableColors: Record<string, string>;
	variableLineStyles: Record<string, string>;
	variableMarkers: Record<string, string>;
	chartType?: 'line' | 'scatter' | 'area';
	autoScale: boolean;
	ymin: number | null;
	ymax: number | null;
	xmin: number | null;
	xmax: number | null;
};

export class ViewerState {
	availableVariables = $state<VariableInfo[]>([]);
	axes = $state<ChartAxis[]>([]);
	loading = $state(false);
	timestep = $state(1);

	chartData = $state<Record<string, Record<string, {x: number[], y: (number | null)[]}>>>({});
	globalChartData = $state<Record<string, Record<string, {x: number[], y: (number | null)[]}>>>({});

	constructor() {
		// Initialize with one empty axis
		this.addAxis();
	}

	async fetchGlobalResults() {
		try {
			await Promise.all(this.axes.map(async ax => {
				if (ax.variables.length === 0) {
					if (this.globalChartData[ax.id]) {
						this.globalChartData[ax.id] = {};
					}
					return;
				}
				
				const { data, error } = await api.POST("/api/v1/simulation/results", {
					body: {
						variables: ax.variables,
						threshold: 1000,
						xmin: null,
						xmax: null
					}
				});
				if (data && typeof data === 'object' && 'data' in data) {
					this.globalChartData[ax.id] = (data as any).data;
				}
			}));
		} catch (e) {
			console.error("Failed to fetch global results", e);
		}
	}

	async fetchVariables() {
		try {
			const { data, error } = await api.GET("/api/v1/simulation/variables");
			if (data) {
				// data is inferred from openapi.json. We cast to VariableInfo[]
				this.availableVariables = data as unknown as VariableInfo[];
			}
		} catch (e) {
			console.error("Failed to load variables", e);
		}
	}

	async fetchResults() {
		this.loading = true;
		try {
			await Promise.all(this.axes.map(async ax => {
				if (ax.variables.length === 0) {
					if (this.chartData[ax.id]) {
						this.chartData[ax.id] = {};
					}
					return;
				}
				
				const { data, error } = await api.POST("/api/v1/simulation/results", {
					body: {
						variables: ax.variables,
						threshold: 1200,
						xmin: ax.xmin,
						xmax: ax.xmax
					}
				});
				if (data && typeof data === 'object' && 'data' in data) {
					this.chartData[ax.id] = (data as any).data;
				}
			}));
		} catch (e) {
			console.error("Failed to fetch results", e);
		} finally {
			this.loading = false;
		}
	}

	addAxis() {
		this.axes.push({
			id: Math.random().toString(36).substring(7),
			variables: [],
			sourceUnits: {},
			targetUnits: {},
			variableColors: {},
			variableLineStyles: {},
			variableMarkers: {},
			chartType: 'line',
			autoScale: true,
			ymin: null,
			ymax: null,
			xmin: null,
			xmax: null
		});
	}

	removeAxis(id: string) {
		this.axes = this.axes.filter(a => a.id !== id);
	}

	setAxisVariables(id: string, variables: string[]) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.variables = variables;
			const tailwindColors = ['#f43f5e', '#f59e0b', '#10b981', '#06b6d4', '#6366f1'];
			variables.forEach((v, idx) => {
				if (!ax.variableColors[v]) {
					ax.variableColors[v] = tailwindColors[idx % tailwindColors.length];
				}
				if (!ax.variableLineStyles[v]) {
					ax.variableLineStyles[v] = 'solid';
				}
				if (!ax.variableMarkers[v]) {
					ax.variableMarkers[v] = 'circle';
				}
			});
			this.fetchGlobalResults();
			this.fetchResults(); // refetch when variables change
		}
	}

	cycleAxisVariableColor(id: string, variable: string) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			const colors = ['#f43f5e', '#f59e0b', '#10b981', '#06b6d4', '#6366f1'];
			const current = ax.variableColors[variable] || colors[0];
			const nextIdx = (colors.indexOf(current) + 1) % colors.length;
			ax.variableColors = { ...ax.variableColors, [variable]: colors[nextIdx === -1 ? 0 : nextIdx] };
			this.axes = [...this.axes];
		}
	}

	cycleAxisVariableLineStyle(id: string, variable: string) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			const styles = ['solid', 'dashed', 'dashdot', 'dotted'];
			const current = ax.variableLineStyles[variable] || styles[0];
			const nextIdx = (styles.indexOf(current) + 1) % styles.length;
			ax.variableLineStyles = { ...ax.variableLineStyles, [variable]: styles[nextIdx === -1 ? 0 : nextIdx] };
			this.axes = [...this.axes];
		}
	}

	cycleAxisVariableMarker(id: string, variable: string) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			const markers = ['circle', 'rect', 'triangle', 'diamond'];
			const current = ax.variableMarkers[variable] || markers[0];
			const nextIdx = (markers.indexOf(current) + 1) % markers.length;
			ax.variableMarkers = { ...ax.variableMarkers, [variable]: markers[nextIdx === -1 ? 0 : nextIdx] };
			this.axes = [...this.axes];
		}
	}

	setAxisVariableUnit(id: string, variable: string, unit: string) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.targetUnits = { ...ax.targetUnits, [variable]: unit };
		}
	}

	setAxisVariableSourceUnit(id: string, variable: string, unit: string) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.sourceUnits = { ...ax.sourceUnits, [variable]: unit };
		}
	}

	setAxisChartType(id: string, type: 'line' | 'scatter' | 'area') {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.chartType = type;
		}
	}

	setAxisAutoScale(id: string, auto: boolean) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.autoScale = auto;
			if (auto) {
				ax.ymin = null;
				ax.ymax = null;
			}
		}
	}

	
	setAxisBounds(id: string, ymin: number | null, ymax: number | null) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.ymin = ymin;
			ax.ymax = ymax;
		}
	}

	setAxisXBounds(id: string, xmin: number | null, xmax: number | null) {
		const ax = this.axes.find(a => a.id === id);
		if (ax) {
			ax.xmin = xmin;
			ax.xmax = xmax;
		}
	}

	async uploadCsv(file: File) {
		const formData = new FormData();
		formData.append('file', file);

		this.loading = true;
		try {
			const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
			const res = await fetch(`${baseUrl}/api/v1/simulation/upload_csv`, {
				method: 'POST',
				body: formData
			});
			if (!res.ok) {
				const errText = await res.text();
				throw new Error(errText);
			}
			// Reset the axes completely
			this.axes = [];
			this.chartData = {};
			this.globalChartData = {};
			this.addAxis(); // re-init with 1 blank axis
			
			// Refetch variables list from newly uploaded DB
			await this.fetchVariables();
			alert('CSV Datastore successfully replaced and loaded!');
		} catch (e: any) {
			console.error('File Upload Failed:', e);
			alert('Upload failed: ' + e.message);
		} finally {
			this.loading = false;
		}
	}
}

// Global instance 
export const viewerState = new ViewerState();
