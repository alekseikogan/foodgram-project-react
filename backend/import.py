import csv, sqlite3

con = sqlite3.connect('db.sqlite3')
cur = con.cursor()
with open('ingredients.csv','r') as fin:
    # csv.DictReader uses first line in file for column headings by default
    dr = csv.DictReader(fin) # comma is default delimiter
    id = 1
    to_db = []
    for i in dr:
        to_db.append(id, i['name'], i['measure'])
        id += 1

cur.executemany('INSERT INTO recipes_ingredient (id, name, measure) VALUES (?, ?, ?);', to_db)
con.commit()
con.close()