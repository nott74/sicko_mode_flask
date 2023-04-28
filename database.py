from flask_sqlalchemy import SQLAlchemy
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv("HOST"))
print(os.getenv("DATABASE"))
print(os.getenv("USER"))
print(os.getenv("PASSWORD"))


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("HOST"),
        database=os.getenv("DATABASE"),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
    )
