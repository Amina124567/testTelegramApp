from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data)
            
            bot_token = os.environ.get('BOT_TOKEN')
            
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                text = update['message'].get('text', '').strip()
                
                if text.startswith('/start'):
                    self.send_welcome_message(chat_id, bot_token)
                elif text.startswith('/help'):
                    self.send_help_message(chat_id, bot_token)
                else:
                    self.send_unknown_command(chat_id, bot_token)
            
            elif 'callback_query' in update:
                callback = update['callback_query']
                chat_id = callback['message']['chat']['id']
                data = callback['data']
                
                requests.post(f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery", 
                            json={'callback_query_id': callback['id']})
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            print(f"Error in bot handler: {e}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

    def send_welcome_message(self, chat_id, bot_token):
        web_app_url = "https://testtelegramapp.vercel.app/"
        
        markup = {
            "inline_keyboard": [
                [{
                    "text": "🌸 Открыть магазин цветов", 
                    "web_app": {"url": web_app_url}
                }],
                [
                    {"text": "📞 Связаться с менеджером", "url": "https://t.me/ImTatyanaSolovyova"}
                ]
            ]
        }
        
        message = "🌸 *Добро пожаловать в магазин элитных цветов!*\n\n✨ У нас вы найдете:\n• Свежие цветы от проверенных поставщиков\n• Красивые букеты для любого случая\n• Индивидуальный подход к каждому заказу\n\nНажмите на кнопку ниже, чтобы открыть каталог и сделать заказ!"
        
        self.send_telegram_message(chat_id, bot_token, message, markup)

    def send_help_message(self, chat_id, bot_token):
        message = "🛠 *Помощь по боту*\n\n*Как сделать заказ:*\n1. Нажмите кнопку «Открыть магазин цветов»\n2. Выберите понравившиеся букеты\n3. Нажмите «Заказать» под товаром\n4. Свяжитесь с менеджером для оформления\n\n*Контакты:*\n📞 Менеджер: @ImTatyanaSolovyova"
        
        self.send_telegram_message(chat_id, bot_token, message)

    def send_unknown_command(self, chat_id, bot_token):
        message = "Извините, я не понимаю эту команду. Используйте /help для получения помощи."
        self.send_telegram_message(chat_id, bot_token, message)

    def send_telegram_message(self, chat_id, bot_token, text, reply_markup=None):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)
            
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running')