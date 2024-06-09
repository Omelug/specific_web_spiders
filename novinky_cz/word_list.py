import sqlite3

conn = sqlite3.connect('results.db')
cursor = conn.cursor()

with open('words.txt', 'r') as file:
    words = [line.strip() for line in file.readlines()]

query = "SELECT * FROM COMMENTS WHERE " + " OR ".join([f"content LIKE '%{word}%'" for word in words])

cursor.execute(query)
results = cursor.fetchall()
for row in results:
    print(row)

conn.close()
