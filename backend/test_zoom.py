import sys
import os
sys.path.append(os.path.abspath('..'))
from backend.features.simulation.service import get_downsampled_data

res = get_downsampled_data(
    variables=["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"],
    threshold=1200,
    xmin=0.0,
    xmax=3.0,
    csv_start_year=2025,
    csv_start_month=1,
    csv_start_day=1,
    csv_end_year=2025,
    csv_end_month=12,
    csv_end_day=31
)

var_res = res["Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"]
x = var_res["x"]
y = var_res["y"]

print(f"Total points returned: {len(x)}")
print(f"First 10 X values: {x[:10]}")
