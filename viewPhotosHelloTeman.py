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
        for message in chat['messages']:
            if message['message_type'] == 'photo':
                sender_id = message['sender_id']
                photo_id = message['photo'][-1]['file_id']  # Mengambil versi foto dengan resolusi tertinggi
                photo_url = get_telegram_file_url(bot_token, photo_id)

                # Mengambil nama lengkap dari koleksi users
                user = users_collection.find_one({ 'user_id': sender_id })
                full_name = user['full_name'] if user else 'Unknown'

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
                <th>Photo</th>
            </tr>
            {% for photo in photos %}
            <tr>
                <td>{{ photo.sender_id }}</td>
                <td>{{ photo.full_name }}</td>
                <td><img src="{{ photo.photo_url }}" alt="Photo" width="100"></td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    
    return render_template_string(html_template, photos=photos_data)

if __name__ == '__main__':
    app.run(debug=True)
