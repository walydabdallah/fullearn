import sqlite3
import os
from flask import Flask, send_file
app = Flask(__name__)

@app.route("/")
def indexPage():
    return send_file("index.html")

@app.route("/<path:path>")
def catchAll(path):
    return send_file(path)

if __name__ == "__main__":
    app.run()
