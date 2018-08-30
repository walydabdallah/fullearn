import sqlite3
from flask import Flask, send_file, url_for, session, request, jsonify, redirect
from flask_oauthlib.client import OAuth
import json
app = Flask(__name__)
app.config['GOOGLE_ID'] = "90702021103-sm9vbhm4o9hbhp8qjfbc88hohanv64p2.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "onx49MjUA-HHD-Ra3IYTYfgo"
app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

def setLoginStatus(contents):
    marker = "<!-- Login Link -->"
    location = contents.find(marker)
    replacement = ""
    if "email" in session:
        emailName = session["email"][ : session["email"].find("@")]
        replacement = '<li class="nav-item"><a class="nav-link" href="/account">{}</a></li>'.format(emailName)
    else:
        replacement = '<li class="nav-item"><a class="nav-link" href="/login">Login</a></li>'
    return contents[ : location] + replacement + contents[location + len(marker) : ]

@app.route("/search")
def searchPage():
    file = open("search.html", "r", encoding="utf8")
    contents = file.read()
    file.close()
    return setLoginStatus(contents)

@app.route("/login")
def loginPage():
    file = open("login.html", "r", encoding="utf8")
    contents = file.read()
    file.close()
    return setLoginStatus(contents)

@app.route('/loginGoogle')
def loginGoogle():
    return google.authorize(callback=url_for('googleAuthorized', _external=True))

@app.route('/loginGoogle/authorized')
def googleAuthorized():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    db = sqlite3.connect("users.db")
    cursor = db.cursor()
    cursor.execute("select id from users where email = '" + me.data["email"] + "';")
    if len(cursor.fetchall()) == 0:
        cursor.execute("select id from users")
        id = 0
        results = cursor.fetchall()
        if len(results) == 0:
            id = 1
        else:
            id = results[-1][0] + 1
        cursor.execute("insert into users values (" + str(id) + ", '" + me.data["email"] + "');")
        db.commit()
    cursor.execute("select id from users where email = '" + me.data["email"] + "';")
    session["user_id"] = cursor.fetchall()[0][0]
    session["email"] = me.data["email"]
    db.close()
    return redirect("/search")

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/logoutGoogle')
def logout():
    session.pop('google_token', None)
    session.pop("user_id", None)
    session.pop("email", None)
    return redirect("/search")

@app.route("/")
def indexPage():
    return redirect("/search")

@app.route("/aboutus")
def aboutPage():
    file = open("aboutus.html", "r", encoding="utf8")
    contents = file.read()
    file.close()
    return setLoginStatus(contents)

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

@app.route("/feedback")
def feedbackPage():
    file = open("feedback.html", "r", encoding="utf8")
    contents = file.read()
    file.close()
    return setLoginStatus(contents)

@app.route("/<path:path>")
def catchAll(path):
    return send_file(path)

if __name__ == "__main__":
    app.run()
