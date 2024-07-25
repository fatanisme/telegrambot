from flask import Flask, render_template_string
import requests
from pymongo import MongoClient
from bottokens import HELLOTEMAN_BOT_TOKEN

app = Flask(__name__)

# Konfigurasi MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['helloteman_db']
chats_collection = db['chats']
users_collection = db['users']

# Fungsi untuk mendapatkan URL file dari Telegram
def get_telegram_file_url(bot_token, file_id):
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(url)
    result = response.json()

    if not result['ok']:
        raise Exception("Failed to get file info")

    file_path = result['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    return file_url

@app.route('/show_photos')
def show_photos():
    bot_token = HELLOTEMAN_BOT_TOKEN

    # Mengambil semua dokumen dari koleksi chats
    chats = chats_collection.find({ "messages.message_type": "photo" })

    # Menyusun data untuk ditampilkan
    photos_data = []
    for chat in chats:
        for message in chat.get('messages', []):
            if message.get('message_type') == 'photo':
                sender_id = message.get('sender_id')
                file_id = message.get('message')  # Mengambil file_id langsung dari message
                
                if not file_id:
                    continue

                try:
                    photo_url = get_telegram_file_url(bot_token, file_id)
                except Exception as e:
                    photo_url = None
                    print(f"Error fetching photo URL: {e}")

                # Mengambil nama lengkap dari koleksi users
                user = users_collection.find_one({ 'user_id': sender_id })
                full_name = user.get('full_name', 'Unknown') if user else 'Unknown'

                photos_data.append({
                    'sender_id': sender_id,
                    'full_name': full_name,
                    'photo_url': photo_url
                })

    # HTML Template
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Photos</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>Telegram Photos</h1>
        <table>
            <tr>
                <th>Sender ID</th>
                <th>Full Name</th>
                <th>Photo URL</th>
            </tr>
            {% for photo in photos %}
            <tr>
                <td>{{ photo.sender_id }}</td>
                <td>{{ photo.full_name }}</td>
                <td>
                    {% if photo.photo_url %}
                        <a href="{{ photo.photo_url }}" target="_blank">{{ photo.photo_url }}</a>
                    {% else %}
                        No Photo Available
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    
    return render_template_string(html_template, photos=photos_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
