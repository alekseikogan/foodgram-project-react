import csv
import sqlite3

con = sqlite3.connect(r'D:/Dev/foodgram-project-react/backend/db.sqlite3')
cur = con.cursor()
with open('D:/Dev/foodgram-project-react/backend/ingredients.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    to_db = []
    for row in reader:
        print(f'Добавляем строку {row["name"]}, {row["measure"]}')
        to_db.append((row['name'], row['measure']))

cur.executemany('INSERT or IGNORE INTO recipes_ingredient (name, measure) VALUES (?, ?);', to_db)
con.commit()
con.close()
