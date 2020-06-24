from flask import Flask, session, render_template, redirect, url_for, request, flash
from flask_session import Session
from forms import RegistrationForm, LoginForm


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