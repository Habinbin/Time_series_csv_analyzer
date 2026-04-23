import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect(":memory:")
df = pd.DataFrame({"A": [1, 2], "B": ["a", "b"], "C": [1.1, 2.2]})
df.to_sql("test", conn, index=False)

df_read = pd.read_sql("SELECT * FROM test LIMIT 1", conn)
print(df_read.dtypes)
print(df_read.select_dtypes(include=[np.number]).columns.tolist())
