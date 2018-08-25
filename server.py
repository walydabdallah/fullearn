import sqlite3
from flask import Flask
app = Flask(__name__)

@app.route("/")
@app.route("/index.html")
def indexPage():
    return send_from_directory("html", "index.html")

if __name__ == "__main__":
    app.run()
