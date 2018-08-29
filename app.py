import sqlite3
from flask import Flask, send_file, request
app = Flask(__name__)

@app.route("/")
def indexPage():
    return send_file("search.html")

@app.route("/notifyme", methods=["POST"])
def preorder():
    db = sqlite3.connect("notify.db")
    cursor = db.cursor()
    name = request.form["name"]
    email = request.form["email"]
    cursor.execute("select id from people;")
    id = len(cursor.fetchall()) + 1
    cursor.execute("insert into people values (" + str(id) + ", '" + name + "', '" + email + "');")
    db.commit()
    db.close()
    return send_file("notifyme.html")

@app.route("/<path:path>")
def catchAll(path):
    return send_file(path)

if __name__ == "__main__":
    app.run()
