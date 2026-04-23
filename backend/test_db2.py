import sqlite3

DB_PATH = "simulation_results.sqlite"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT rowid, * FROM ashpb_pv_ess_1yr LIMIT 5")
rows = cursor.fetchall()
print("First 5 rows in SQLite:")
for row in rows:
    print(row)
conn.close()
