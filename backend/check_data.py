import pandas as pd
df = pd.read_csv('/home/habin/Codes/Time_series_csv_analyzer/eplusout.csv')
col = 'Environment:Site Direct Solar Radiation Rate per Area [W/m2](Hourly)'
print("Total rows:", len(df))
print("Number of non-zero points:", (df[col] > 0).sum())
print("Number of peaks (roughly days with solar):", ((df[col] > 0) & (df[col].shift(1) == 0)).sum())
