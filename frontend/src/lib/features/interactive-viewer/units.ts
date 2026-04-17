export interface UnitGroup {
    name: string;
    units: Record<string, number>; // value * factor = value_in_base
}

export const unitGroups: Record<string, UnitGroup> = {
    power: { 
        name: 'Power', 
        units: { 'W': 1, 'kW': 1000, 'MW': 1e6, 'GW': 1e9 } 
    },
    flow: { 
        name: 'Volumetric Flow', 
        units: { 'm3/s': 1, 'L/min': 1/60000, 'm3/h': 1/3600 } 
    },
    pressure: { 
        name: 'Pressure', 
        units: { 'Pa': 1, 'kPa': 1000, 'MPa': 1e6, 'GPa': 1e9, 'bar': 100000 } 
    },
    mass_flow: { 
        name: 'Mass Flow', 
        units: { 'kg/s': 1, 'kg/h': 1/3600 } 
    },
    enthalpy: { 
        name: 'Spec. Enthalpy', 
        units: { 'J/kg': 1, 'kJ/kg': 1000, 'MJ/kg': 1e6 } 
    },
    temperature: { 
        name: 'Temperature', 
        units: { 'C': 1, 'K': 1 } // simple 1:1, ignore offset for now
    }
};

export function getUnitGroupKey(unit: string): string | null {
    for (const [key, group] of Object.entries(unitGroups)) {
        if (unit in group.units) return key;
    }
    return null;
}

export function getAvailableConversions(unit: string): string[] {
	const groupKey = getUnitGroupKey(unit);
	if (!groupKey) return [];
	return Object.keys(unitGroups[groupKey].units);
}

export function convertValue(value: number, fromUnit: string, toUnit: string): number {
	if (fromUnit === toUnit) return value;
	const groupKey = getUnitGroupKey(fromUnit);
	if (!groupKey) return value;
	
    const group = unitGroups[groupKey];
    if (!(toUnit in group.units)) return value;
    
    // Convert to base unit first, then to target unit
    const baseValue = value * group.units[fromUnit];
    return baseValue / group.units[toUnit];
}
