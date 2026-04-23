import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "simulation_results.sqlite"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT rowid, \"Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)\" FROM ashpb_pv_ess_1yr LIMIT 100", conn)
print(df)
y = df.iloc[:, 1].values
print("Values:")
print(y)

try:
    y_float = y.astype(float)
    mask = np.isfinite(y_float)
    print("Mask:", mask)
    print("Clean count:", np.sum(mask))
except Exception as e:
    print("Error:", e)
conn.close()
