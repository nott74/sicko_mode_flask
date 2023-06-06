import os
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("HOST"),
        database=os.getenv("DATABASE"),
        user=os.getenv("USERID"),
        password=os.getenv("PASSWORD")
    )
