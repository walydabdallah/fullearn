import sqlite3
from flask import Flask, send_file, url_for, session, request, jsonify, redirect
from flask_oauthlib.client import OAuth
import json
import google_scrape
import math
import operator

app = Flask(__name__)
app.config['GOOGLE_ID'] = "90702021103-sm9vbhm4o9hbhp8qjfbc88hohanv64p2.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "onx49MjUA-HHD-Ra3IYTYfgo"
app.secret_key = 'development'
oauth = OAuth(app)

websites = ["reddit", "quora", "bodybuilding.com", "gamespot", "ign", "neogaf", "studentroom"]

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

@app.route("/search", methods=["GET", "POST"])
def searchPage():
    file = open("search.html", "r", encoding="utf8")
    contents = file.read()
    file.close()
    contents = setLoginStatus(contents)

    if request.method == "GET":
        return contents

    marker = "<!-- Search Results -->"
    location = contents.find(marker)
    replacement = ""

    db = sqlite3.connect("alexaranks.db")
    cursor = db.cursor()
    search_results = []
    for site in websites:
        cursor.execute("select rank from ranks where website = '" + site + "';")
        alexa_rank = cursor.fetchall()[0][0]
        scraped = google_scrape.scrape_google(request.form["query"] + " " + site, int(10.0 * 2.0 / math.log(alexa_rank, 10)), "en")
        print(len(scraped))
        for result in scraped:
            result["rank"] = result["rank"] * math.log(alexa_rank, 10)
        search_results.extend(scraped)

    search_results.sort(key=operator.itemgetter('rank'))

    db.close()
    for result in search_results:
        validResult = False
        for site in websites:
            if result["link"].find(site) != -1:
                validResult = True
                break

        if not validResult:
            continue
        if result["description"] == None:
            continue

        replacement += '<div class="col-sm-6 col-lg-4 mb-4">'
        replacement += '<div class="blog-entry">'
        replacement += '<div class="blog-entry-text">'
        title_text = result["title"][ : 75]
        if len(result["title"]) > 75:
            title_text += " ..."
        if len(title_text) < 79:
            title_text += "&nbsp; " * (79 - len(title_text))
        replacement += '<h3><a href="{}">{}</a></h3>'.format(result["link"], title_text)
        post_text = result["description"][ : 150]
        if len(result["description"]) > 150:
            post_text += " ..."
        if len(post_text) < 154:
            post_text += "&nbsp; " * (154 - len(post_text))
        replacement += '<p class="mb-4">{}</p>'.format(post_text)
        replacement += '<div class="meta">'
        replacement += '<a href="#">Fullearn Score: {} </a>'.format(str(round(result["rank"], 4)))
        replacement += '</div></div></div></div>'
    return contents[ : location] + replacement + contents[location + len(marker) : ]


@app.route("/login")
def loginPage():
    file = open("login.html", "r", encoding="utf8")
    contents = file.read()
    file.close()
    return setLoginStatus(contents)

@app.route("/hashTest/<password>")
def hashTest(password):
    return str(hashPassword(password))

def hashPassword(password):
    hash = 0
    for i in range(0, len(password)):
        hash += ord(password[i])
    return hash

@app.route("/loginNormal")
def loginNormal():
    db = sqlite3.connect("users.db")
    cursor = db.cursor()
    password = request.args["password"]
    email = request.args["email"]
    cursor.execute("select * from users where email = " + "'" + email + "';")

    userEntry = cursor.fetchall()
    db.close()
    if len(userEntry) == 0:
        return "Invalid email address"
    userEntry = userEntry[0]
    if userEntry[2] == "google":
        return "Please login with Google instead"
    if hashPassword(password) == userEntry[1]:
        session["email"] = userEntry[0]
        return redirect("/search")
    else:
        return "Wrong password"

@app.route("/createAccount", methods=["GET", "POST"])
def createAccount():
    if request.method == "GET":
        file = open("createaccount.html", "r", encoding="utf8")
        contents = file.read()
        file.close()
        return setLoginStatus(contents)
    else:
        db = sqlite3.connect("users.db")
        cursor = db.cursor()
        password = request.form["password"]
        email = request.form["email"]
        cursor.execute("select * from users where email = '" + email + "';")
        userEntry = cursor.fetchall()

        # If the email address already exists in the database
        if len(userEntry) > 0:
            return "There is already an account associated with this email address."

        hash = hashPassword(password)

        cursor.execute("insert into users values ('" + email + "', '" + str(hash) + "', 'normal');")
        db.commit()
        db.close()
        return redirect("/login")


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
    cursor.execute("select * from users where email = " + "'" + me.data["email"] + "';")
    if len(cursor.fetchall()) == 0:
        cursor.execute("insert into users values ('" + me.data["email"] + "', 0, 'google');")
        db.commit()
    session["email"] = me.data["email"]
    db.close()
    return redirect("/search")

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/logoutGoogle')
def logout():
    session.pop('google_token', None)
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
