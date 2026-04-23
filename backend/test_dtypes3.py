import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect(":memory:")
df = pd.DataFrame({"A": [1, 2], "B": ["a", "b"], "C": [1.1, 2.2]})
df.to_sql("test", conn, index=False)

schema_df = pd.read_sql("PRAGMA table_info(test)", conn)
print(schema_df)
