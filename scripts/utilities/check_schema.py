import sqlite3

conn = sqlite3.connect('tbcv.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(recommendations)')
print('Recommendations table columns:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

conn.close()
