import os
import telebot
import threading
import time
from telebot import types
import sqlite3
from config import API_TOKEN

# Создаем бота
bot = telebot.TeleBot(token=API_TOKEN)

# Подключаемся к базе данных SQLite
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, username TEXT, chat_id INTEGER)''')
conn.commit()

# Функция для получения всех пользователей из базы данных
def get_all_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return users

# Функция для отправки сообщения каждые 5 минут

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    global conn, cursor
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id

    # Добавляем пользователя в базу данных
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, chat_id) VALUES (?, ?, ?)',
                   (user_id, username, chat_id))
    conn.commit()

    # Создаем клавиатуру
    markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton('Написать админу', callback_data='write_admin')
    url_button = types.InlineKeyboardButton('Моё био', url='https://t.me/KriminalowBIO')
    markup.add(itembtn1, url_button)
    # Отправляем фото и приветственное сообщение с клавиатурой
    bot.send_photo(chat_id, open('fff.jpg', 'rb'), caption=f"Приветствую @{username}, ты попал в мой сапорт бот. ПИСАТЬ ТОЛЬКО ПО  ДЕЛУ!!!", reply_markup=markup)

# Обработчик нажатия кнопки "Написать админу"
@bot.callback_query_handler(func=lambda call: call.data == "write_admin")
def handle_write_admin(call):
    msg = bot.send_message(call.message.chat.id, "Напишите вашу просьбу-предложения и в скором времени вам ответят:")
    bot.register_next_step_handler(msg, send_to_admin, call.from_user.id, call.from_user.username)

# Функция для отправки сообщения админу
def send_to_admin(message, user_id, username):
    admin_chat_id = 6448857134  # Замените на ваш ID чата с админом
    user_message = message.text

    # Отправляем пользователю подтверждение об отправке сообщения
    bot.send_message(message.chat.id, "Сообщение отправлено")

    # Создаем клавиатуру с кнопкой "Ответить"
    markup = types.InlineKeyboardMarkup()
    itembtn1 = types.InlineKeyboardButton('Ответить', callback_data=f'reply_{user_id}')
    markup.add(itembtn1)

    # Отправляем сообщение админу с информацией о пользователе и кнопкой "Ответить"
    bot.send_message(admin_chat_id, f"Сообщение от @{username} (ID: {user_id}):\n\n{message.text}", reply_markup=markup)

# Обработчик кнопки "Ответить"
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply'))
def handle_reply(call):
    user_id = int(call.data.split('_')[1])  # Извлекаем идентификатор пользователя из данных обратного вызова
    msg = bot.send_message(call.message.chat.id, "Введите текст:")
    bot.register_next_step_handler(msg, send_reply, user_id)

# Функция для отправки ответа пользователю
def send_reply(message, user_id):
    # Отправляем введенный пользователем текст пользователю с заданным идентификатором
    bot.send_message(user_id, message.text)
    # Отправляем сообщение админу о том, что ответ был отправлен
    bot.send_message(6448857134, "Ответ был отправлен.")

# Обработчик команды /admin
@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Проверяем, является ли пользователь админом (замените на свою логику проверки)
    if user_id == 6448857134:
        # Создаем клавиатуру с кнопками админ-панели
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Рассылка")
        item2 = types.KeyboardButton("Статистика пользователей")
        markup.add(item1, item2)

        # Отправляем сообщение с админ-панелью
        admin_message = "Добро пожаловать в админ-панель! Выберите действие:"
        bot.send_message(chat_id, admin_message, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Извините, у вас нет доступа к админ-панели.")

# Обработчик кнопки "Рассылка"
@bot.message_handler(func=lambda message: message.text == "Рассылка")
def handle_broadcast(message):
    msg = bot.reply_to(message, "Введите текст для рассылки:")
    bot.register_next_step_handler(msg, send_broadcast)

# Функция для рассылки сообщения всем пользователям
def send_broadcast(message):
    # Получаем список всех пользователей из базы данных
    users = get_all_users()

    # Отправляем сообщение каждому пользователю
    for user in users:
        user_id, username, chat_id = user
        bot.send_message(chat_id, message.text)

# Обработчик кнопки "Статистика пользователей"
@bot.message_handler(func=lambda message: message.text == "Статистика пользователей")
def handle_user_stats(message):
    # Получаем список всех пользователей из базы данных
    users = get_all_users()

    # Формируем сообщение со статистикой пользователей
    user_stats = ""
    for user in users:
        user_id, username, chat_id = user
        user_stats += f"Username: @{username}, User ID: {user_id}\n"

    # Отправляем статистику пользователей пользователю
    bot.send_message(message.chat.id, user_stats)

# Запускаем бота
bot.polling(none_stop=True)
