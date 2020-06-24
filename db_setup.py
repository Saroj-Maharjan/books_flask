from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(sessionmaker(bind=engine, autocommit= False, autoFlush = False))

Base = declarative_base()

Base.query = db_session.query_property()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)