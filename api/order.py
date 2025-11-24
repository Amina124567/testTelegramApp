from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import sys

sys.path.append(os.path.dirname(__file__))

try:
    from supabase_client import supabase
except ImportError as e:
    print(f"Import error: {e}")

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        try:
            user_id = self.headers.get('User-Id', '')
            is_admin = self.headers.get('Is-Admin', 'false') == 'true'
            
            if is_admin:
                orders_response = supabase.table("orders").select("*").execute()
                statuses_response = supabase.table("order_statuses").select("*").execute()
                
                orders = orders_response.data
                statuses = statuses_response.data
                
                status_map = {status['id']: status for status in statuses}
                
                for order in orders:
                    status_info = status_map.get(order['status_id'])
                    if status_info:
                        order['status_name'] = status_info['name']
                        order['status_color'] = status_info['color']
            else:
                response = supabase.table("orders").select("*").eq("user_id", user_id).execute()
                orders = response.data
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(orders).encode('utf-8'))
            
        except Exception as e:
            print(f"Error in order GET handler: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_PUT(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            order_data = json.loads(post_data)
            
            order_id = order_data.get('order_id')
            status_id = order_data.get('status_id')
            
            if not order_id:
                raise ValueError("Order ID is required")
            
            update_data = {'status_id': status_id}
            
            response = supabase.table("orders").update(update_data).eq("id", order_id).execute()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {'success': True, 'message': 'Order updated successfully'}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            print(f"Error in order PUT handler: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            order_data = json.loads(post_data)
            
            db_success = self.save_order_to_db(order_data)
            
            if db_success:
                admin_success = self.send_admin_notification(order_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {'success': True, 'message': 'Order processed successfully'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Error in order POST handler: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_DELETE(self):
        try:
            path_parts = self.path.split('/')
            order_id = path_parts[-1] if path_parts[-1] else path_parts[-2]
            
            if not order_id.isdigit():
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'success': False, 'error': 'Invalid order ID'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            response = supabase.table("orders").delete().eq("id", int(order_id)).execute()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {'success': True}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            print(f"Error in order DELETE handler: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def send_admin_notification(self, order_data):
        try:
            bot_token = os.environ.get('BOT_TOKEN')
            
            admins_response = supabase.table("admins").select("telegram_id").eq("is_active", True).execute()
            admin_chat_ids = [admin['telegram_id'] for admin in admins_response.data]
            
            if not bot_token or not admin_chat_ids:
                print("Missing BOT_TOKEN or no active admins")
                return False
            
            clean_phone = order_data['phone'].replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            telegram_link = f"tg://openmessage?user_id={order_data['user']['id']}"
            phone_link = f"https://t.me/+{clean_phone}" if clean_phone.startswith('7') else f"https://t.me/+7{clean_phone}"
            
            items_text = "\n".join([
                f"• {item['name']} - {item['quantity']} шт. × {item['price']} ₽ = {item['total']} ₽" 
                for item in order_data['items']
            ])
            
            cart_total = order_data['total']
            
            message = f"""🎉 *НОВЫЙ ЗАКАЗ!*

👤 *Информация о клиенте:*
🆔 ID: `{order_data['user']['id']}`
📛 Имя: {order_data['user']['first_name']}
👤 Юзернейм: @{order_data['user']['username']}
📞 Телефон: `{clean_phone}`

🛍️ *Состав заказа:*
{items_text}

💎 *Итого к оплате:* {cart_total} ₽

📋 *Комментарий:* {order_data.get('comment', 'Нет комментария')}

🕐 *Время заказа:* {order_data['time']}

💬 *Связаться с клиентом:*
[📱 По ID]({telegram_link}) | [☎️ По номеру]({phone_link})"""
            
            success_count = 0
            for admin_chat_id in admin_chat_ids:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': admin_chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True,
                    'reply_markup': {
                        'inline_keyboard': [[
                            {'text': '📱 Написать по ID', 'url': telegram_link},
                            {'text': '☎️ Написать по номеру', 'url': phone_link}
                        ]]
                    }
                }
                
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error sending admin notification: {e}")
            return False

    def save_order_to_db(self, order_data):
        try:
            clean_phone = order_data['phone'].replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            
            cart_total = order_data['total']
            
            order_record = {
                "user_id": str(order_data['user']['id']),
                "user_name": order_data['user']['first_name'],
                "user_username": order_data['user'].get('username', ''),
                "phone": clean_phone,
                "comment": order_data.get('comment', ''),
                "items": order_data['items'],
                "total_amount": cart_total,
                "final_amount": cart_total,
                "status_id": 1
            }
            
            result = supabase.table("orders").insert(order_record).execute()
            print(f"Order saved to DB with ID: {result.data[0]['id'] if result.data else 'Unknown'}")
            return True
            
        except Exception as e:
            print(f"Error saving order to DB: {e}")
            return False