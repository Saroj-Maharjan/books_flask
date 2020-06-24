from application import db

class users(db.Model):
    __table_name__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(60),nullable=False)