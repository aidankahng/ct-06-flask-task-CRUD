import os

# Get the base directory of this folder
# os.path.abs() <- get absolute path
# os.path.dirname() <- get path to directory of name
# __file__ this file's name
basedir = os.path.abspath(os.path.dirname(__file__)) 

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "app.db")