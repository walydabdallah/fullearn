import sqlite3
from flask import Flask, send_file
app = Flask(__name__)

@app.route("/")
def indexPage():
    return send_file("landing.html")

@app.route("/preorder")
def preorder():
    return send_file("html/ltr/vertical-menu-template/coming-soon.html")

@app.route("/<path:path>")
def catchAll(path):
    return send_file(path)

if __name__ == "__main__":
    app.run()
