import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "simulation_results.sqlite"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT rowid, \"PERIMETER_ZN_2:Zone Mean Radiant Temperature [C](Hourly)\" FROM ashpb_pv_ess_1yr", conn)
print(f"Total rows in DB: {len(df)}")

y = df.iloc[:, 1].values
# count peaks
peaks = 0
for i in range(1, len(y)-1):
    if y[i] > y[i-1] and y[i] > y[i+1]:
        peaks += 1
print(f"Number of peaks in raw data: {peaks}")

import lttb
data = np.stack([np.arange(len(y)), y], axis=1)
downsampled = lttb.downsample(data, n_out=1000)
y_ds = downsampled[:, 1]
peaks_ds = 0
for i in range(1, len(y_ds)-1):
    if y_ds[i] > y_ds[i-1] and y_ds[i] > y_ds[i+1]:
        peaks_ds += 1
print(f"Number of peaks in LTTB downsampled data (1000 points): {peaks_ds}")
conn.close()
