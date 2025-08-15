import threading
import sqlite3



thread_local = threading.local()


def get_connection():
    if not hasattr(thread_local, 'connection'):
        thread_local.connection = sqlite3.connect('database.db', check_same_thread=False)
    return thread_local.connection

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS switches (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            check_interval INTEGER,
            last_check INTEGER,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            switch_id INTEGER,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()



def add_switch(user_id, message, check_interval, last_check, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO switches (user_id, message, check_interval, last_check, password) VALUES (?, ?, ?, ?, ?)", (user_id, message, check_interval, last_check, password))
    conn.commit()
    switch_id = cursor.lastrowid
    return switch_id


def remove_switch(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM switches WHERE ID=?", (id,))
    conn.commit()

def add_contact(switch_id, email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO contacts (switch_id, email) VALUES (?,?)", (switch_id, email))
    conn.commit()

def remove_contact(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE ID=?", (id,))
    conn.commit()


def remove_contact_from_switch(switch_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE switch_id=?", (switch_id,))
    conn.commit()


def get_switches_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM switches WHERE user_id=?", (user_id,))
    return cursor.fetchall()

def get_contacts_switch(switch_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts WHERE switch_id=?", (switch_id,))
    return cursor.fetchall()
