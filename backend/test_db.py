import sqlite3

DB_PATH = "simulation_results.sqlite"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM ashpb_pv_ess_1yr")
n_total = cursor.fetchone()[0]
print(f"n_total in SQLite: {n_total}")
conn.close()
