import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# database engine object from SQLAlchemy that manages connections to the database
engine = create_engine(os.getenv("DATABASE_URL"))

# create a 'scoped session' that ensures different users' interactions with the
# database are kept separate
db = scoped_session(sessionmaker(bind=engine))

# class User(db.model):
#     id = db.Column(db.integer, primary_key=True)
#     fname = db.Column(db.String(20), unique=True, nullable=False)
#     lname = db.Column(db.String(20), unique=True, nullable=False)
#     username = db.Column(db.String(20), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(60), nullable=False)

#     def __repr__(self):
#         return f"User('{self.fname}','{self.lname}','{self.username}','{self.email}')"

# class Books(db.model):
#     id = db.Column(db.Integer, primary_key=True)
#     isbn = db.Column(db.string(40), unique=True, nullable=False)
#     title = db.Column(db.String(50), nullable=False)
#     author = db.Column(db.String(50), nullable=False)
#     year = db.Column(db.String(10), nullable=False)

# class BookDATA(db.model):
#     f = open("books.csv")
#     reader = csv.reader(f)
#     for isbn, title, author, year in reader:
#         db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
#                     {"isbn": isbn,
#                     "title": title,
#                     "author": author,
#                     "year": year})

#         print(f"Added book {title} to database.")
#         db.commit()


def main():
    # db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, fname VARCHAR NOT NULL, lname VARCHAR NOT NULL, username VARCHAR NOT NULL, email VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    # db.execute("CREATE TABLE reviews (id SERIAL PRIMARY KEY, book_id INTEGER NOT NULL,\
    #     user_id INTEGER NOT NULL, comment VARCHAR NOT NULL,\
    #     rating INTEGER NOT NULL, timestamp timestamp default current_timestamp)")
    db.execute("DROP TABLE IF EXISTS \"books\"")
    db.execute("CREATE TABLE books (book_id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL,title VARCHAR NOT NULL,author VARCHAR NOT NULL,year VARCHAR NOT NULL)")
    
    with open('books.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)

        for isbn, title, author, year in csvreader:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                        {"isbn": isbn, 
                        "title": title,
                        "author": author,
                        "year": year})

            print(f"Added book {title} to database.")
            db.commit()


if __name__ == "__main__":
    main()
