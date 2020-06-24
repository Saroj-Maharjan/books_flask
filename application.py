import os

from flask import Flask, session, render_template, redirect, url_for, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from forms import RegistrationForm, LoginForm, SearchForm

from passlib.hash import sha256_crypt
from helpers import login_required


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
    return render_template("dashboard.html", form=form)

@app.route("/about")
def about():
    return "Test"
  
@app.route("/login", methods=["GET", "POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
        account=db.execute(
            "SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()

        if account is None:
            flash("No username", "danger")

        else:
            if sha256_crypt.verify(password, account['password']):
                session["loggedin"]=True
                session["user_id"]=account["id"]
                session["username"]=account["username"]
                flash('You have been logged in!', 'success')
                # Redirect to home page
                return redirect(url_for("index"))
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template("login.html", title="Login", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form=RegistrationForm()
    if form.validate_on_submit():
        username=form.username.data
        fname=form.fname.data
        lname=form.lname.data
        email=form.email.data
        password=form.password.data
        secure_password=sha256_crypt.encrypt(str(password))

        account=db.execute(
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

@app.route("/search", methods=["GET"])
@login_required
def search():
    form = SearchForm()
    """ Get books results """
    # Check book id was provided
    if form.validate_on_submit():
        search = form.search.data

        books = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 15",
                        {"query": query}).fetchAll()
        if books in None:
            flash(f'No Book Found {form.search.data}!')
            return redirect(url_for("index"))
        else:
            return render_template("result.html",books=books)
    return redirect(url_for('index'))


