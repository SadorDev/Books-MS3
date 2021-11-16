import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
     import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)

@app.route("/")
@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template("home.html")


# User Registration 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check to see if password exists within the database
        existing_user = mongo.db.users.find_one(
            {"users": request.form.get("email").lower()})

        if existing_user:
                flash("email already exists")
                return redirect(url_for("register"))

        register =  {
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # Put the session user into a session cookie 
        session["user"] = request.form.get("email").lower()
        flash("Registration successful")
        return redirect(url_for("account", email=session["email"]))

    return render_template("register.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method =="POST":
        # Check if Email exists 
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        # print(existing_user)
        if existing_user:
            # Ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["email"] = request.form.get("email").lower()
                    flash("Welcome, {}" .format(request.form.get("email")))
                    return redirect(url_for(
                        "account", email=session["email"]))
            else:
                # Invalid password match
                flash("Incorrect Password")
                return redirect(url_for("login"))
        else:
            # Email doesn't exist
            flash("Email doesn't exist")
            return redirect(url_for("login"))

    return render_template("login.html")

# User log in
@app.route("/account/<email>", methods=["GET", "POST"])
def account(email):
    # checks if user is logged in
    if session.get("user"):
        # grab the session user's email from the db
        email = mongo.db.users.find_one(
            {"email": session["user"]})["email"]
        # display users book reviews and favourites on account page
        if session["user"] == email:
            books = list(mongo.db.books.find({"created_by": email}))
            favourites = list(mongo.db.bookmarked.find(
                {"created_by": email}))
            return render_template("account.html", books=books,
                                   email=email)
    # if user is not logged in. if different user is logged in,
    # their own account will be loaded
    else:
        flash("You need to be logged in to perform this action")
        return redirect(url_for("login"))

    return render_template("login.html")


# User Logging Out
@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("Log Out Successful")
    session.pop("email")
    return redirect(url_for("login"))


# Add Book to database
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    # checks if user is logged in
    if session.get("user"):
        if request.method == "POST":
            # purchase link auto-generated
            purchase_link = (
                "https://www.amazon.co.uk/s?k=" +
                request.form.get("book_title")
            )
            # retrieve book info from form
            book = {
                "book_title": request.form.get("book_title"),
                "author": request.form.get("author"),
                "genre": request.form.get("genre_type"),
                "release_year": request.form.get("release_year"),
                "image_url": request.form.get("image_url"),
                "rating": request.form.get("rating"),
                "book_review": request.form.get("book_review"),
                "purchase_link": purchase_link,
                "created_by": session["user"]
            }
            # insert new book into db
            mongo.db.books.insert_one(book)
            flash("Book Review Added!")
            return redirect(url_for("books"))
        categories = mongo.db.categories.find().sort("category_name", 1)
        return render_template("add_book.html", categories=categories)
    # if user is not logged in
    else:
        flash("You need to be logged in to perform this action")
        return redirect(url_for("login"))

    
if __name__== "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True) # debug should be = false when submitting. Only true when testing your application
        