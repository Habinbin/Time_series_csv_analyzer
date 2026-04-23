import sys
import os
sys.path.append(os.path.abspath('..'))
from backend.features.simulation.service import get_downsampled_data

res = get_downsampled_data(
    variables=["PERIMETER_ZN_2:Zone Mean Radiant Temperature [C](Hourly)"],
    threshold=500,
    xmin=0,
    xmax=4,
    csv_start_year=2025,
    csv_start_month=1,
    csv_start_day=1,
    csv_end_year=2025,
    csv_end_month=12,
    csv_end_day=31
)

var_res = res["PERIMETER_ZN_2:Zone Mean Radiant Temperature [C](Hourly)"]
x = var_res["x"]
y = var_res["y"]

print(f"Total points returned: {len(x)}")
print(f"First 10 X values: {x[:10]}")
print(f"Diffs: {[x[i] - x[i-1] for i in range(1, 10)]}")
