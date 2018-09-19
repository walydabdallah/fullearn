import urllib, sys, bs4
print(bs4.BeautifulSoup(urllib.urlopen("http://data.alexa.com/data?cli=10&dat=s&url="+ 'https://www.reddit.com/').read(), "xml").find("REACH")['RANK'])

db = sqlite3.connect("alexaranks.db")
cursor = db.cursor()

cursor.execute("delete from ranks;")

alexa_rank = seo.get_alexa('https://www.reddit.com/')
cursor.execute("insert into ranks values ('reddit', " + str(alexa_rank) + ");")

alexa_rank = seo.get_alexa('https://www.quora.com/')
cursor.execute("insert into ranks values ('quora', " + str(alexa_rank) + ");")

alexa_rank = seo.get_alexa('https://www.bodybuilding.com/')
cursor.execute("insert into ranks values ('bodybuilding.com', " + str(alexa_rank) + ");")

db.commit()
db.close()
