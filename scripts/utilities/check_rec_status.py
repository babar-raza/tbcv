import sqlite3

conn = sqlite3.connect('tbcv.db')
cursor = conn.cursor()

cursor.execute('SELECT status, COUNT(*) FROM recommendations WHERE created_at > datetime("now", "-15 minutes") GROUP BY status')
print('Recommendation statuses (last 15 min):')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
