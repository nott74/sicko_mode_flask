from flask_sqlalchemy import SQLAlchemy
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("HOST"),
        database=os.getenv("DATABASE"),
        user=os.getenv("USERID"),
        password=os.getenv("PASSWORD")
    )
