import sqlite3

conn = sqlite3.connect('tbcv.db')
cursor = conn.cursor()

# Validation status breakdown
cursor.execute('SELECT status, COUNT(*) FROM validation_results WHERE created_at > datetime("now", "-10 minutes") GROUP BY status')
print('Validation status breakdown:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Sample recommendations with validation status
cursor.execute('SELECT validation_id, status FROM recommendations WHERE created_at > datetime("now", "-10 minutes") LIMIT 5')
print('\nSample recommendations with validation status:')
for row in cursor.fetchall():
    cursor.execute('SELECT status FROM validation_results WHERE id=?', (row[0],))
    vr = cursor.fetchone()
    print(f'  Recommendation for validation {row[0]} (rec_status={row[1]}), validation status={vr[0] if vr else "NOT FOUND"}')

conn.close()
