import openai
import sqlite3
import requests
from datetime import date
import logging
import traceback

class GPTQuery:
    def __init__(self, db_name):
        self.dbname = f'{db_name}.db'
        self.user_lvl = 50
        self.gpt_lvl = 51
        self.history_lvl = 52
        logging.addLevelName(self.user_lvl, 'User')
        logging.addLevelName(self.gpt_lvl, 'ChatGPT')
        logging.addLevelName(self.history_lvl, 'История')
        logging.basicConfig(level=logging.CRITICAL, filename=f"bot.log", format='%(asctime)s - %(levelname)s: %(message)s')

    def show_model(self, user_id: int):
        try:
            with sqlite3.connect(self.dbname) as conn:
                cur = conn.cursor()
                cur.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, reg DATE, total_req INTEGER, model TEXT)')
                cur.execute('INSERT OR IGNORE INTO users (tg_id, reg, total_req, model) VALUES (?, ?, ?, ?)', (user_id, date.today(), 0, 'gpt-3.5-turbo'))
                current_model = cur.execute('SELECT model FROM users WHERE tg_id = ?', (user_id,)).fetchone()

                return current_model[0] if current_model else 'Модель не установлена'
        except:
            logging.critical(traceback.format_exc())

    def set_model(self, model: str, user_id: int):
        try:
            with sqlite3.connect(self.dbname) as conn:
                cur = conn.cursor()
                cur.execute('UPDATE users SET model = ? WHERE tg_id = ?', (model, user_id))
                conn.commit()
                logging.log(self.user_lvl, f'{user_id} сменил модель на {model}')
        except:
            logging.critical(traceback.format_exc())

    def insert_into_history(self, user_id: int, request: str, response: str):
        try:
            with sqlite3.connect(f'{user_id}_history.db') as conn:
                cur = conn.cursor()
                cur.execute(f'CREATE TABLE IF NOT EXISTS user_{user_id} (id INTEGER PRIMARY KEY, Requests TEXT, Responses TEXT)')
                cur.execute(f'INSERT INTO user_{user_id} (Requests, Responses) VALUES (?, ?)', (request, response))
                conn.commit()
        except:
            logging.critical(traceback.format_exc())

    def create_message(self, message: str, user_id: int):
        try:       
            history = []
            with sqlite3.connect(f'{user_id}_history.db') as con:
                cur = con.cursor()
                cur.execute(f'CREATE TABLE IF NOT EXISTS user_{user_id}(id INTEGER PRIMARY KEY, Requests TEXT, Responses TEXT)')
                last_requests = cur.execute(f'SELECT Requests FROM user_{user_id} ORDER BY id').fetchall()
                last_responses = cur.execute(f'SELECT Responses FROM user_{user_id} ORDER BY id').fetchall()

                for request, response in zip(last_requests, last_responses):
                    if request:
                        history.append({"role": "user", "content": request[0]})
                    if response:
                        history.append({"role": "assistant", "content": response[0]})
                history.append({"role": "user", "content": message})
            logging.log(self.history_lvl, history)
            return history
        except:
            logging.critical(traceback.format_exc())

    def delete_context(self, user_id: int):
        try:
            with sqlite3.connect(f'{user_id}_history.db') as conn:
                cur = conn.cursor()
                cur.execute(f'DELETE FROM user_{user_id}')
                conn.commit()
            logging.log(self.user_lvl, f'{user_id} стер историю')
        except:
            logging.critical(traceback.format_exc())

    def profile(self, user_id: int):
        try:
            with sqlite3.connect(self.dbname) as conn:
                cur = conn.cursor()
                cur.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, reg DATE, total_req INTEGER, model TEXT)')
                user_info = cur.execute('SELECT tg_id, reg, total_req, model FROM users WHERE tg_id = ?', (user_id,)).fetchone()
                tg_id, reg_date, total_requests, model = user_info
                profile_message = f"User ID: {tg_id}\nДата регистрации: {reg_date}\nВсего запросов: {total_requests}\nМодель: {model}"
                return profile_message if user_info else "Пользователь не найден"
        except:
            logging.critical(traceback.format_exc())

    def create_request(self, request: str, user_id: int):
        try:
            logging.log(self.user_lvl, request)
            with sqlite3.connect(self.dbname) as conn:
                cur = conn.cursor()
                cur.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, reg DATE, total_req INTEGER, model TEXT)')
                user_record = cur.execute('SELECT * FROM users WHERE tg_id = ?', (user_id,)).fetchone()
                if user_record is None:
                    cur.execute('INSERT INTO users (tg_id, reg, total_req, model) VALUES (?, ?, ?, ?)',
                                (user_id, date.today(), 1, 'gpt-3.5-turbo'))
                else:
                    cur.execute('UPDATE users SET total_req = total_req + 1 WHERE tg_id = ?', (user_id,))
                conn.commit()
                user_message = self.create_message(request, user_id)
                prompt = openai.chat.completions.create(
                    model = self.show_model(user_id),
                    max_tokens = 900,
                    temperature = 0.7,
                    messages = user_message,
                )
                response = prompt.choices[0].message.content
                logging.log(self.gpt_lvl, response)
                self.insert_into_history(user_id, request, response)
                return response
        except:
            logging.critical(traceback.format_exc())

    def generate_image(self, client, request: str, user_id: int):
        try:
            response = client.images.generate(
                model = "dall-e-2",
                prompt = request,
                size = '512x512',
                quality = "standard",
                n = 1,)
            image_url = response.data[0].url
            image_name = f'{image_url[-5:]}.png'
            image_file = requests.get(image_url)
            with open(image_name, 'wb') as f:
                f.write(image_file.content)
            return image_name
        except:
            logging.critical(traceback.format_exc())
    
    def logging(self, function: str, error):
        logging.critical(f"Ошибка в {function}: {error}")