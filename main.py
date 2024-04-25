import telebot
from telebot import types
import openai
from openai import OpenAI
#Нужно создать файл tokens.py и в нем указать токены от телеграм бота и OpenAI API в переменные tg_token и gpt_token
from tokens import gpt_token, tg_token
from gpt_api import GPTQuery
import random
import traceback

bot = telebot.TeleBot(tg_token)
openai.api_key = gpt_token
client = OpenAI(api_key = gpt_token)
chat = GPTQuery('Data')

emoji_list = ["🧐", "😎", "🤓", "😊", "👍", "🌟", "🤖", "😎", "🚀", "👏", "🎉", "💡", "🔍", "💼",
    "📚", "💻", "🎨", "🚗", "🍕", "☕", "🏆", "🎸", "🌍"]
admin = [] #В этом списке указать свой ID

@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(message.chat.id, "Это бот с ChatGPT. Чтобы задать вопрос, просто напиши его.")
    except:
        chat.logging('start', traceback.format_exc())

@bot.message_handler(commands=['dell'])
def dell(message):
    try:
        chat.delete_context(message.from_user.id)
        bot.reply_to(message, f'{"🗑️"} История чата удалена')
    except:
        chat.logging('dell', traceback.format_exc())

@bot.message_handler(commands=['profile'])
def profile(message):
    try:
        bot.send_message(message.chat.id, chat.profile(message.from_user.id))
    except:
        chat.logging('profile', traceback.format_exc())

@bot.message_handler(commands=['model'])
def set_model(message):
    try:
        markup_inline = types.InlineKeyboardMarkup()
        btn_gpt_3_5 = types.InlineKeyboardButton(text="GPT-3.5 Turbo", callback_data='gpt_3_5')
        markup_inline.add(btn_gpt_3_5)
        btn_gpt_4 = types.InlineKeyboardButton(text="GPT-4 Turbo", callback_data='gpt_4_turbo')
        markup_inline.add(btn_gpt_4)
        bot.send_message(message.chat.id, "Выберите модель:", reply_markup=markup_inline)
    except:
        chat.logging('set_model', traceback.format_exc())

@bot.message_handler(func=lambda message: True if message.text[:4].strip() == '/img' else False)
def img(message):
    try:
        image_response = message.text[5:].strip()
        wait_message = bot.reply_to(message, f'{random.choice(emoji_list)} Изображение генерируется...')
        response = chat.generate_image(client, image_response, message.from_user.id)
        bot.delete_message(message.chat.id, wait_message.message_id)
        photo = open(response, 'rb')
        try:
            bot.send_photo(message.chat.id, photo, caption = image_response)
        except:
            bot.send_photo(message.chat.id, photo)
        photo.close()
    except:
        chat.logging('handle_message', traceback.format_exc())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        wait_message = bot.reply_to(message, f'{random.choice(emoji_list)} Запрос на обработке...')
        bot.send_chat_action(message.chat.id, 'typing')
        response = chat.create_request(message.text, message.from_user.id)
        bot.delete_message(message.chat.id, wait_message.message_id)
        bot.send_message(message.chat.id, response, parse_mode="markdown")
    except:
        chat.logging('handle_message', traceback.format_exc())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        if call.data == 'gpt_3_5':
            chat.set_model('gpt-3.5-turbo-0125', call.from_user.id)
            bot.send_message(call.message.chat.id, f'🔍 Модель сменена на GPT-3.5 Turbo')
        elif call.data == 'gpt_4_turbo':
            chat.set_model('gpt-4-1106-preview', call.from_user.id)
            bot.send_message(call.message.chat.id, f'💡 Модель сменена на GPT-4 Turbo')
    except:
        chat.logging('callback', traceback.format_exc())

bot.polling()