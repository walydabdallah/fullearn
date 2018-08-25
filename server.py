import sqlite3
from flask import Flask, send_file
app = Flask(__name__)

@app.route("/<path:path>")
def catchAll(path):
    if path == "":
        return send_file("index.html")
    return send_file(path)

if __name__ == "__main__":
    app.run()
