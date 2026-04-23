import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import lttb
import io

DB_PATH = Path(__file__).resolve().parent.parent.parent / "simulation_results.sqlite"

def get_variables():
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    # Read the table schema to identify column types
    schema_df = pd.read_sql("PRAGMA table_info(ashpb_pv_ess_1yr)", conn)
    conn.close()
    
    if schema_df.empty:
        return []

    # Filter out columns that are text-based (like Date/Time)
    numeric_cols = []
    for _, row in schema_df.iterrows():
        col_name = row['name']
        col_type = str(row['type']).upper()
        # pandas to_sql typically maps to TEXT, REAL, INTEGER
        if not ('TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type or 'BLOB' in col_type):
            numeric_cols.append(col_name)
    
    vars_info = []
    for col in numeric_cols:
        if "[" in col and "]" in col:
            name, unit_str = col.split("[", 1)
            name = name.strip()
            unit = unit_str.replace("]", "").strip()
            vars_info.append({"name": name, "unit": unit, "raw_col": col})
        else:
            vars_info.append({"name": col, "unit": "", "raw_col": col})
            
    return vars_info

import datetime

def get_downsampled_data(variables: list[str], threshold: int, xmin: float | None = None, xmax: float | None = None, csv_start_year: int = 2025, csv_start_month: int = 1, csv_start_day: int = 1, csv_end_year: int = 2025, csv_end_month: int = 12, csv_end_day: int = 31) -> dict:
    """
    Reads the requested variables from SQLite and applies LTTB downsampling.

    xmin / xmax are fractional ratios in [0.0, 1.0] representing the slice
    position within the *entire* dataset (n_total rows). They are completely
    independent of the date-range parameters, which are used only to compute
    the X-axis label scale (minutes_per_point).
    """
    if not DB_PATH.exists():
        return {}

    # Read data
    conn = sqlite3.connect(DB_PATH)
    
    # Secure column names (prevent basic injection by checking against available)
    avail_cols = [v["raw_col"] for v in get_variables()]
    safe_vars = [v for v in variables if v in avail_cols]
    
    if not safe_vars:
        conn.close()
        return {}
        
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ashpb_pv_ess_1yr")
    n_total = cursor.fetchone()[0]
    
    # Calculate span_days: used ONLY for X-axis label scaling, not for slicing.
    try:
        st_date = datetime.datetime(csv_start_year, csv_start_month, csv_start_day)
        en_date = datetime.datetime(csv_end_year, csv_end_month, csv_end_day)
        span_days = max(1, (en_date - st_date).days + 1)
    except ValueError:
        span_days = 365  # Default fallback on invalid date

    # xmin / xmax are 0.0–1.0 ratios of the *full* dataset.
    # Slicing is always relative to n_total, never to span_days.
    min_idx = max(0, int(xmin * n_total)) if xmin is not None else 0
    max_idx = min(n_total, int(xmax * n_total)) if xmax is not None else n_total
    
    if min_idx < max_idx:
        # Avoid loading everything! Load only targeted rowids (1-indexed in SQLite)
        query = f"SELECT rowid, {', '.join([f'{chr(34)}{v}{chr(34)}' for v in safe_vars])} FROM ashpb_pv_ess_1yr WHERE rowid > {min_idx} AND rowid <= {max_idx}"
        df = pd.read_sql(query, conn)
    else:
        # Load empty dataframe schema
        query = f"SELECT rowid, {', '.join([f'{chr(34)}{v}{chr(34)}' for v in safe_vars])} FROM ashpb_pv_ess_1yr LIMIT 0"
        df = pd.read_sql(query, conn)

    conn.close()

    n_rows = len(df)
    results = {}
    
    if n_rows <= 11520: # 8 days of 1 minute data (allow buffer around 7 days zoom)
        use_lttb = False
    elif n_rows <= threshold * 4: # Small enough to return raw or apply mild
        use_lttb = False
    else:
        use_lttb = True

    # Map each row to a minute value on the X axis.
    # total_minutes = the full date-range span expressed in minutes so that
    # the X-axis labels (formatted from startDate) align correctly regardless
    # of the actual data density.
    total_minutes = span_days * 1440.0
    minutes_per_point = total_minutes / n_total if n_total > 0 else 1.0
    
    # Time array (X axis) proxy - convert rowid to conceptual simulation minutes
    if n_rows > 0:
        x = (df['rowid'].values - 1).astype(np.float64) * minutes_per_point
    else:
        x = np.array([], dtype=np.float64)
    
    for col in safe_vars:
        y = df[col].astype(float).values
        # @python-data-analysis: Handle NaNs and Infs numerically to prevent JSONResponse breakage
        mask = np.isfinite(y)
        x_clean = x[mask]
        y_clean = y[mask]
        
        if use_lttb and len(x_clean) > threshold:
            # lttb expects shape (N, 2)
            data = np.stack([x_clean, y_clean], axis=1)
            try:
                downsampled = lttb.downsample(data, n_out=threshold)
                x_ds = downsampled[:, 0]
                y_ds = downsampled[:, 1]
            except Exception as e:
                # Fallback to simple slicing if LTTB fails (e.g., too few points)
                x_ds = x_clean[::n_rows//threshold]
                y_ds = y_clean[::n_rows//threshold]
        else:
            x_ds = x_clean
            y_ds = y_clean
            
        results[col] = {"x": x_ds.tolist(), "y": y_ds.tolist()}
        
    return results

from typing import BinaryIO

def process_csv_upload(file_obj: BinaryIO) -> dict:
    """
    Reads CSV file object in chunks and replaces the simulation_results.sqlite data 
    minimizing memory usage and preventing 'too many SQL variables' errors.
    """
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Drop the table if it exists to ensure purely fresh data
    cursor.execute("DROP TABLE IF EXISTS ashpb_pv_ess_1yr")
    conn.commit()

    chunksize = 20000  # Process in chunks to save memory and avoid SQLite variable limits
    first_chunk = True
    cols = []
    
    try:
        # Read the file directly from the SpooledTemporaryFile object in chunks
        for chunk in pd.read_csv(file_obj, chunksize=chunksize):
            if first_chunk:
                # first chunk: create table and store column names
                chunk.to_sql("ashpb_pv_ess_1yr", conn, if_exists="replace", index=False)
                cols = list(chunk.columns)
                first_chunk = False
            else:
                # subsequent chunks: append to exactly the same table
                chunk.to_sql("ashpb_pv_ess_1yr", conn, if_exists="append", index=False)
    except Exception as e:
        conn.close()
        raise ValueError(f"Failed to parse CSV: {e}")
        
    if first_chunk:
        conn.close()
        raise ValueError("The uploaded CSV is empty.")
        
    conn.close()
    
    return {"message": "CSV uploaded and datastore replaced successfully", "columns_detected": len(cols)}
