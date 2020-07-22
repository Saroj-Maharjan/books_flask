import os

from flask import Flask, session, render_template, redirect, url_for, request, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from forms import RegistrationForm, LoginForm, SearchForm, BookDetailForm

from passlib.hash import sha256_crypt
from helpers import login_required

import requests


app = Flask(__name__)
# secret key
app.config['SECRET_KEY'] = '4b6d5f03d66f02693e774a24cff3f2d1'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# goodread api
# res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "Ph0EuZD75IDuHEVx5VQKAg", "isbns": "9781632168146"})


@app.route("/")
@login_required
def index():
    form = SearchForm()
    if request.args.get("book"):
        text = request.args.get("book")
         # Take input and add a wildcard
        query = f"%{text}%".lower()

        rows = db.execute("SELECT book_id, isbn, title, author, year FROM books WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search",
                            {"search": query})

        # Books not founded
        if rows.rowcount == 0:
            flash(
                f'No Book Found "{request.args.get("book")}" Try Again !!', 'danger')
            return redirect(url_for('index'))

        # Fetch all the results
        books = rows.fetchall()

        return render_template("dashboard.html", title="Home", form=form, books=books)

    return render_template("dashboard.html", title="Home", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("loggedin"):
        flash("You are already logged in", "danger")
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        account = db.execute(
            "SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()

        if account is None:
            flash("No username", "danger")

        else:
            if sha256_crypt.verify(password, account['password']):
                session["loggedin"] = True
                session["user_id"] = account["id"]
                session["username"] = account["username"]
                flash('You have been logged in!', 'success')
                # Redirect to home page
                return redirect(url_for("index"))
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template("login.html", title="Login", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("loggedin"):
        flash("You are already logged in", "danger")
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        fname = form.fname.data
        lname = form.lname.data
        email = form.email.data
        password = form.password.data
        secure_password = sha256_crypt.encrypt(str(password))

        account = db.execute(
            "SELECT * FROM users where username = :username OR email = :email", {"username": username, "email": email}).fetchone()

        if account is None:
            db.execute("INSERT into users(fname, lname, username, email, password) VALUES (:fname, :lname, :username, :email, :password)", {
                "fname": fname, "lname": lname, "username": username, "email": email, "password": secure_password})
            db.commit()
            flash(f'Account created for {form.username.data}!')
            return redirect(url_for("login"))
        else:
            flash("user already existed, please login or contact admin", "danger")
            return redirect(url_for('login'))

    return render_template("register.html", title="Register", form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logout successful")
    return redirect(url_for('index'))


@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book(book_id):
    form = BookDetailForm()
    row = db.execute("SELECT * FROM books WHERE book_id =:id",
                         {"id": book_id})
    bookInfo = row.fetchall()

    if form.validate_on_submit():
        # Save current user info
        currentUser = session["user_id"]

        # Fetch form data
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        # Check for user submission (ONLY 1 review/user allowed per book)
        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                    {"user_id": currentUser,
                     "book_id": bookInfo[0]['book_id']})
        # A review already exists
        if row2.rowcount == 1:
            flash('You already submitted a review for this book', 'warning')
            return redirect( url_for('book', book_id = bookInfo[0]['book_id']))
        
        rating = int(rating)
        db.execute("INSERT INTO reviews (user_id, book_id, comment, rating) VALUES \
                    (:user_id, :book_id, :comment, :rating)",
                    {"user_id": currentUser, 
                    "book_id": bookInfo[0]['book_id'], 
                    "comment": comment, 
                    "rating": rating})
        # Commit transactions to DB and close the connection
        db.commit()

        flash('Review submitted!', 'info')

        return redirect( url_for('book', book_id = bookInfo[0]['book_id']))


    """ GOODREADS reviews """
    query = requests.get("https://www.goodreads.com/book/review_counts.json",
                        params={"key": "Ph0EuZD75IDuHEVx5VQKAg", "isbns": bookInfo[0]['isbn']})
    
    #Convert and clean the response
    response = query.json()
    response = response['books'][0]

    bookInfo.append(response)

    """ Users reviews """
    reviews = db.execute(
        "SELECT reviews.comment, users.username, reviews.timestamp, reviews.user_id, reviews.rating FROM reviews \
        LEFT JOIN users ON reviews.user_id = users.id \
        WHERE reviews.book_id=:id",
        {"id": bookInfo[0]['book_id']}).fetchall()

    return render_template("detail.html", form=form, book = bookInfo , reviews = reviews, title= bookInfo[0]['title'])


@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api_call(isbn):

    # COUNT returns rowcount
    # SUM returns sum selected cells' values
    # INNER JOIN associates books with reviews tables

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.book_id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    # Error checking
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    # Fetch result from RowProxy    
    tmp = row.fetchone()

    # Convert to dict
    result = dict(tmp.items())

    # Round Avg Score to 2 decimal. This returns a string which does not meet the requirement.
    # https://floating-point-gui.de/languages/python/
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)