import sqlite3

conn = sqlite3.connect('tbcv.db')
cursor = conn.cursor()

cursor.execute('SELECT status, COUNT(*) FROM recommendations GROUP BY status')
print('All recommendation statuses:')
total = 0
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')
    total += row[1]
print(f'Total: {total}')

# Check most recent recommendations
cursor.execute('SELECT id, status, title, created_at FROM recommendations ORDER BY created_at DESC LIMIT 10')
print('\n10 Most recent recommendations:')
for row in cursor.fetchall():
    print(f'  {row[3]} - Status: {row[1]} - {row[2][:50]}...')

conn.close()
