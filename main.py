import requests
import telebot
from telebot import types
import os
import sqlite3
import threading
import time
import re


BOT_TOKEN = os.environ.get('BOT_TOKEN')
START_MESSAGE = """
DeadManSend is a free, open-source Telegram bot designed to ensure your safety and peace of mind. Set a custom check-in interval, and if you don’t respond with a predefined password within the specified time, DeadManSend will automatically send a pre-defined alert message to your chosen contacts via email.
Key Features:

- Fully Automated: Set your check-in frequency and forget—DeadManSend handles the rest.
- Password Verification: At each check-in, you must enter a predefined password to confirm you are safe.
- Email Alerts: Alerts are sent via email to your emergency contacts.
- Privacy-First: Your data is never shared or stored unnecessarily. All messages are secured with encryption.
- Open Source: Transparent, community-driven, and always free.

How It Works:

1. Set your check-in interval (e.g., every 24 hours).
2. Define a predefined password for verification.
3. Add your emergency contacts email addresses  and customize your alert message.
4. At each interval, DeadManSend will prompt you to enter the password via Telegram.
5. If you miss a check-in or enter the wrong password, DeadManSend notifies your contacts automatically by email.

For more information, support, or to contribute, contact me at @judemont or visit futureofthe.tech.
"""

# Thread-local storage for the database connection
thread_local = threading.local()

def get_db_connection():
    if not hasattr(thread_local, 'connection'):
        thread_local.connection = sqlite3.connect('database.db', check_same_thread=False)
    return thread_local.connection

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS switches (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            check_interval INTEGER,
            last_check INTEGER
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



def add_switch_db(user_id, message, check_interval, last_check):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO switches (user_id, message, check_interval, last_check) VALUES (?, ?, ?, ?)", (user_id, message, check_interval, last_check))
    conn.commit()
    switch_id = cursor.lastrowid
    return switch_id


def remove_switch_db(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM switches WHERE ID=?", (id,))
    conn.commit()

def add_contact_db(switch_id, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO contacts (switch_id, email) VALUES (?,?)", (switch_id, email))
    conn.commit()

def remove_contact_db(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE ID=?", (id,))
    conn.commit()


def get_switches_user_db(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM switches WHERE user_id=?", (user_id,))
    return cursor.fetchall()

def get_contacts_switch_db(switch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts WHERE switch_id=?", (switch_id,))
    return cursor.fetchall()


# def set_interval(func, sec):
#     def func_wrapper():
#         set_interval(func, sec)
#         func()
#     t = threading.Timer(sec, func_wrapper)
#     t.start()
#     return t    


def is_email_valid(email):
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)
    return valid


if __name__ == "__main__":
    create_table()

    bot = telebot.TeleBot(BOT_TOKEN)
    user_states = {}
    
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        newCheckBtn = types.KeyboardButton('/new')
        myChecksBtn = types.KeyboardButton('/list')
        markup.add(newCheckBtn, myChecksBtn)
        bot.send_message(message.chat.id, START_MESSAGE, reply_markup=markup)

    
    @bot.message_handler(commands=['new'])
    def user_new(message):
        user_id = message.from_user.id
        user_states[user_id] = {"step": "interval"}

        bot.reply_to(message, "What verification interval (number of days) ? ")



    @bot.message_handler(func=lambda message: True)
    def handle_user_reply(message):
        user_id = message.from_user.id
        if user_id not in user_states:
            return  

        user_state = user_states[user_id]
        current_step = user_state["step"]

        if current_step == "interval":
            try:
                interval_days = int(message.text)
                if interval_days <= 0:
                    raise ValueError
                user_state["interval"] = interval_days
                user_state["step"] = "password"
                bot.reply_to(message, "Set a predefined password for verification (you'll need to enter it at each check-in):")
            except ValueError:
                bot.reply_to(message, "Please enter a valid number of days (e.g., 1, 3, 7):")

        elif current_step == "password":
            user_state["password"] = message.text
            user_state["step"] = "message"
            bot.reply_to(message, "Enter the alert message to send to your contacts if you miss a check-in:")

        elif current_step == "message":
            user_state["alert_message"] = message.text
            user_state["step"] = "contacts"
            bot.reply_to(message, "Add your emergency contacts email. Send one contact email per message. Send 'done' when finished:")

        elif current_step == "contacts":
            if message.text.lower() == "done":
                if "contacts" not in user_state or not user_state["contacts"]:
                    bot.reply_to(message, "No contacts added. Please add at least one contact.")
                    return

                save_check_in(
                    user_id=user_id,
                    interval=user_state["interval"],
                    password=user_state["password"],
                    alert_message=user_state["alert_message"],
                    contacts=user_state["contacts"]
                )

                bot.reply_to(message, "Your check-in is set up! You'll be asked for your password every {} days.".format(user_state["interval"]))
                del user_states[user_id]  
            else:
                if "contacts" not in user_state:
                    user_state["contacts"] = []
                if not is_email_valid(message.text):
                    bot.reply_to(message, "Invalid email address")
                else:
                    user_state["contacts"].append(message.text)
                    bot.reply_to(message, "Contact added. Send another contact email or 'done' to finish:")



    def save_check_in(user_id, interval, password, alert_message, contacts):
  

        switch_id = add_switch_db(user_id, alert_message, interval, int(time.time()))
        
        
        for contact in contacts:
            add_contact_db(switch_id, contact)
   




    # set_interval(check_websites, 300)
    bot.infinity_polling()