import requests
import telebot
from telebot import types
import os
import time
import re
import db
import hashlib
from dotenv import load_dotenv, dotenv_values 




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



def hash_password(password):
    pwd_salt = password + HASH_SALT
    hashed = hashlib.sha256(pwd_salt.encode())
    has_hex = hashed.hexdigest()

def save_check_in(user_id, interval, password, alert_message, contacts):
    password_hshd = hash_password(password)
    switch_id = db.add_switch(user_id, alert_message, interval, int(time.time()), password_hshd)
    
    
    for contact in contacts:
        db.add_contact(switch_id, contact)


if __name__ == "__main__":
    load_dotenv() 

    BOT_TOKEN = os.getenv('BOT_TOKEN')
    HASH_SALT = os.getenv('HASH_SALT')


    db.create_table()
    bot = telebot.TeleBot(BOT_TOKEN)
    user_states = {}
    
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        switches = db.get_switches_user(user_id)

        markup = types.ReplyKeyboardMarkup(row_width=2)

        if len(switches) == 0:
            btn1 = types.KeyboardButton('/new')
        else:
            btn1 = types.KeyboardButton('/delete')

        markup.add(btn1)
        bot.send_message(message.chat.id, START_MESSAGE, reply_markup=markup)

    
    @bot.message_handler(commands=['new'])
    def user_new(message):
        user_id = message.from_user.id
        user_states[user_id] = {"step": "interval"}

        bot.reply_to(message, "What verification interval (number of days) ? ")



    @bot.message_handler(commands=['delete'])
    def user_new(message):
        user_id = message.from_user.id
        user_states[user_id] = {"step": "delete"}

        markup = types.ReplyKeyboardMarkup(row_width=2)

        btn1 = types.KeyboardButton('yes')
        btn1 = types.KeyboardButton('no')

        bot.reply_to(message, "Are you sure you want to delete your automatic check-in and pre-recorded message ?", reply_markup=markups)
        


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
                bot.send_message(message.chat.id, "Set a predefined password for verification (you'll need to enter it at each check-in):")
            except ValueError:
                bot.reply_to(message, "Please enter a valid number of days (e.g., 1, 3, 7):")

        elif current_step == "password":
            user_state["password"] = message.text
            time.sleep(1.2)
            bot.delete_message(message.chat.id, message.message_id)
            user_state["step"] = "message"
            bot.send_message(message.chat.id, "Enter the alert message to send to your contacts if you miss a check-in:")

        elif current_step == "message":
            user_state["alert_message"] = message.text
            user_state["step"] = "contacts"
            bot.send_message(message.chat.id, "Add your emergency contacts email. Send one contact email per message. Send 'done' when finished:")

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

                bot.send_message(message.chat.id, "Your check-in is set up! You'll be asked for your password every {} days.".format(user_state["interval"]))
                del user_states[user_id]  
            else:
                if "contacts" not in user_state:
                    user_state["contacts"] = []
                if not is_email_valid(message.text):
                    bot.reply_to(message, "Invalid email address")
                else:
                    user_state["contacts"].append(message.text)
                    bot.reply_to(message, "Contact added. Send another contact email or 'done' to finish:")

        elif current_step == "delete":
            if message.text.lower() == "yes":
                switches = get_switches_user_db(user_id)
                for switch in switches:
                    db.remove_switch(switch["ID"])
                    db.remove_contact_from_switch(switch["ID"])
                bot.send_message(message.chat.id, "Done !")

            elif message.text.lower() == "no":
                bot.send_message(message.chat.id, "Ok.")

                
        



    # set_interval(check_websites, 300)
    bot.infinity_polling()