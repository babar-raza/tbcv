"""Get details of approved recommendations for testing enhancement."""
import sqlite3

conn = sqlite3.connect('tbcv.db')
cursor = conn.cursor()

# Get an approved recommendation with file path
cursor.execute('''
    SELECT r.id, r.validation_id, r.title, v.file_path
    FROM recommendations r
    LEFT JOIN validation_results v ON r.validation_id = v.id
    WHERE r.status = 'APPROVED'
    LIMIT 3
''')

print("Approved recommendations for enhancement testing:\n")
for rec_id, val_id, title, file_path in cursor.fetchall():
    print(f"Recommendation ID: {rec_id}")
    print(f"Validation ID: {val_id}")
    print(f"File Path: {file_path}")
    print(f"Title: {title}")
    print("-" * 80)
    print()

conn.close()
