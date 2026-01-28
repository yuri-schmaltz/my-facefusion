
import sqlite3
import json

db_path = '.jobs/orchestrator.db'
job_id = 'job-20260128-182703-4630345b'

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT metadata_json FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    
    if row and row['metadata_json']:
        metadata = json.loads(row['metadata_json'])
        if 'traceback' in metadata:
            print("--- TRACEBACK ---")
            print(metadata['traceback'])
        else:
            print("No traceback found in metadata.")
            print(f"Metadata keys: {list(metadata.keys())}")
    else:
        print("Job or metadata not found.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
