from datetime import datetime
import os
import sqlite3
from time import localtime, strftime


DATABASE = './data/swaks.db'


def get_conn():
    return sqlite3.connect('./data/swaks.db')


def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE mail_record
    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SUBJECT TEXT NOT NULL,
    MAIL_TO CHAR(255) NOT NULL,
    DATETIME DATETIME NOT NULL,
    STATUS CHAR(10) NOT NULL)
    ''')


def insert_record(subject, mail_to, status):
    conn = get_conn()
    cursor = conn.cursor()
    datetime = strftime('%Y-%m-%d %H:%M:%S', localtime())
    cursor.execute(f'INSERT INTO mail_record (SUBJECT, MAIL_TO, DATETIME, STATUS) VALUES (\'{subject}\', \'{mail_to}\', \'{datetime}\', \'{status}\')')
    conn.commit()


if not os.path.isfile(DATABASE):
    init_db()
