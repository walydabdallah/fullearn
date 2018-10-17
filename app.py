import sqlite3
from flask import Flask, url_for, session, request, redirect, send_file
from flask_oauthlib.client import OAuth
import google_scrape
import math
import operator
from google import google

app = Flask(__name__)
app.config['GOOGLE_ID'] = "90702021103-sm9vbhm4o9hbhp8qjfbc88hohanv64p2.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "onx49MjUA-HHD-Ra3IYTYfgo"
app.secret_key = 'development'
oauth = OAuth(app)

# Allows for Google authentication
googleAuth = oauth.remote_app(
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

# List of source websites that Fullearn collects answers from
websites = ["reddit", "quora", "bodybuilding.com", "gamespot", "neogaf", "studentroom"]

db = sqlite3.connect("alexaranks.db")
cursor = db.cursor()
cursor.execute("select * from ranks;")
results = cursor.fetchall()

# This dictionary will store each website and its corresponding Alexa rank
alexaRanks = {}

# Builds up the alexaRanks dictionary with provides a mapping from each website name to its corresponding Alexa rank
for website, rank in results:
    alexaRanks[website] = rank

db.close()

# The max length for the title and body of each search result flashcard. If title/body exceeds max, then we add '...'
# and skip the characters that exceed the limit
titleMaxLen = 75
bodyMaxLen = 150

# Read in the contents of an HTML page and returns a string containing the HTML code
def readPage(page):
    file = open(page, "r", encoding="utf8")
    contents = file.read()
    file.close()
    return contents

# Takes an HTML page in the form of a string containing the HTML code, and displays the user's name if he/she is logged in
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

# The page that contains the search bar and displays the search results
@app.route("/search", methods=["GET", "POST"])
def searchPage():
    contents = setLoginStatus(readPage("search.html"))

    if request.method == "GET":
        return contents

    # The following section handles what happens when something is actually submitted using the search bar (POST request)

    marker = "<!-- Search Results -->"
    location = contents.find(marker)
    replacement = ""

    search_results = []
    for site in websites:
        # If the question is 'How to get a girlfriend' and the website that we are currently collecting from is reddit
        # we'd ask on Google 'how to get a girlfriend reddit'
        # The number of results to scrape from Google is calculated using 10 * 2 / log(AlexaRank)
        response = google.search(request.form["query"] + " " + site)
        # The Google results are already ranked from 1 to say, 10, obviously. We now multiply these ranks by log(AlexaRank) so that
        # less popular websites (which would have higher Alexa rank therefore) have their ranks increased relative to popular, low Alexa rank
        # websites. This allows answers from more popular websites to have lower rank values and thus get displayed first on the page.
        for result in response:
            result.index = (result.index + 1) * math.log(alexaRanks[site], 10)
            result.name = result.name[ : result.name.find("http")]
        search_results.extend(response)

    # By this point search_results contains all the results from all the different source websites
    # Having calculated the new rankings using the Alexa algorithm, sort all the search results by this rank
    search_results.sort(key=lambda x: x.index)

    for result in search_results:
        # Google search results with no description tend to be advertised ones hence we ignore them since their format is different compared
        # to standard search results.
        if result.description == None:
            continue

        validResult = False
        # When searching 'how to get a girlfriend reddit' on Google not all the results are even going to be from reddit. So by checking
        # whether reddit is in the URL allows us to filter out the non-reddit results. Same idea for all the other sites we're collecting from.
        for site in websites:
            if result.link.find(site) != -1:
                validResult = True
                break

        if not validResult:
            continue

        replacement += '<div class="col-sm-6 col-lg-4 mb-4">'
        replacement += '<div class="blog-entry">'
        replacement += '<div class="blog-entry-text">'

        # Appends '...' when the title exceeds the max length
        title_text = result.name[ : titleMaxLen]
        if len(result.name) > titleMaxLen:
            title_text += " ..."

        # To ensure that each flashcard displays with the same dimensions, we add white space so that all flashcard titles have the same length
        if len(title_text) < titleMaxLen + 4:
            title_text += "&nbsp; " * (titleMaxLen + 4 - len(title_text))

        replacement += '<h3><a href="{}">{}</a></h3>'.format(result.link, title_text)

        # Appends '...' when the flashcard body exceeds the max length
        post_text = result.description[ : bodyMaxLen]
        if len(result.description) > bodyMaxLen:
            post_text += " ..."

        # To ensure that each flashcard displays with the same dimensions, we add white space so that all flashcard bodies have the same length
        if len(post_text) < bodyMaxLen + 4:
            post_text += "&nbsp; " * (bodyMaxLen + 4 - len(post_text))

        replacement += '<p class="mb-4">{}</p>'.format(post_text)
        replacement += '<div class="meta">'

        # Displays score produced by the Alexa algorithm on the flashcard for debugging purposes, might be best to remove in production build
        replacement += '<a href="#">Fullearn Score: {} </a>'.format(str(round(result.index, 4)))

        replacement += '</div></div></div></div>'
    return contents[ : location] + replacement + contents[location + len(marker) : ]

# This URL displays the user the login form
@app.route("/login")
def loginPage():
    return setLoginStatus(readPage("login.html"))

# Hashes the password so that we can safely store the hash in the database without storing the original password
def hashPassword(password):
    hash = 0
    for i in range(0, len(password)):
        hash += ord(password[i])
    return hash

# Allows us to input a password into the URL and test what our hashing function hashes it to
@app.route("/hashTest/<password>")
def hashTest(password):
    return str(hashPassword(password))

# Is called when the user wishes to login normally with an account created on Fullearn.com
@app.route("/loginNormal")
def loginNormal():
    db = sqlite3.connect("users.db")
    cursor = db.cursor()
    password = request.args["password"]
    email = request.args["email"]
    # Gets all users in the database with the given email address
    cursor.execute("select * from users where email = " + "'" + email + "';")
    userEntry = cursor.fetchall()
    db.close()

    # No users with this email clearly means that it's a invalid email address
    if len(userEntry) == 0:
        return "Invalid email address"

    # Email address must be valid if it passed the above test
    userEntry = userEntry[0]

    # If someone created the account by login in with Google previously, we tell them to login with Google instead
    if userEntry[2] == "google":
        return "Please login with Google instead"

    # Checks password and logs them in if password is correct
    if hashPassword(password) == userEntry[1]:
        session["email"] = userEntry[0]
        return redirect("/search")
    else:
        return "Wrong password"

# Allows users to create accounts on fullearn.com
@app.route("/createAccount", methods=["GET", "POST"])
def createAccount():
    # Retrieves the account creation form
    if request.method == "GET":
        return setLoginStatus(readPage("createaccount.html"))
    else: # POST request, handles when the user actually uses the form to submit details
        db = sqlite3.connect("users.db")
        cursor = db.cursor()
        password = request.form["password"]
        email = request.form["email"]
        cursor.execute("select * from users where email = '" + email + "';")
        userEntry = cursor.fetchall()

        # If the email address already exists in the database, tell the user
        if len(userEntry) > 0:
            return "There is already an account associated with this email address."

        # Stores the email address along with the hashed password in users.db
        hash = hashPassword(password)
        cursor.execute("insert into users values ('" + email + "', '" + str(hash) + "', 'normal');")
        db.commit()
        db.close()
        return redirect("/login")

# Handles Google authentication
@app.route('/loginGoogle')
def loginGoogle():
    return googleAuth.authorize(callback=url_for('googleAuthorized', _external=True))

@app.route('/loginGoogle/authorized')
def googleAuthorized():
    resp = googleAuth.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    # Stores Google access token in the session so that we can make Google API calls
    session['google_token'] = (resp['access_token'], '')

    # Gets the Google user profile from the Google API
    me = googleAuth.get('userinfo')

    db = sqlite3.connect("users.db")
    cursor = db.cursor()
    # Try to check if there's any user account with this Google email address
    cursor.execute("select * from users where email = " + "'" + me.data["email"] + "';")
    # If there is currently no account with this email address, create a new entry in users.db specifying that it's a Google account
    if len(cursor.fetchall()) == 0:
        cursor.execute("insert into users values ('" + me.data["email"] + "', 0, 'google');")
        db.commit()
    # If the user has already created a normal Fullearn account with the same email address, we log them in anyway. This allows Fullearn
    # users to allow in to their accounts both via Google, and via normal Fullearn login
    session["email"] = me.data["email"]
    db.close()
    return redirect("/search")

# Retrieves the Google access token used to perform Google API calls
@googleAuth.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

# Logs out by clearing the current login session
@app.route('/logout')
def logout():
    session.pop('google_token', None)
    session.pop("email", None)
    return redirect("/search")

@app.route("/")
def indexPage():
    return redirect("/search")

@app.route("/aboutus")
def aboutPage():
    return setLoginStatus(readPage("aboutus.html"))

@app.route("/feedback")
def feedbackPage():
    return setLoginStatus(readPage("feedback.html"))

# Any URL not handled by the above '@app.route's is handled here. Most importantly
# this allows additional resources like images and CSS files to be provided to the browser upon request
@app.route("/<path:path>")
def catchAll(path):
    return send_file(path)

if __name__ == "__main__":
    app.run()
