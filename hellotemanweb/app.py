import sys
import os
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from math import ceil
import requests
from bson import ObjectId
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bottokens import HELLOTEMAN_BOT_TOKEN, LOGIN_USERNAME, LOGIN_PASSWORD

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfigurasi MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['helloteman_db']
users_collection = db['users']
user_pairs_collection = db['user_pairs']
chats_collection = db['chats']

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Kelas User
class User(UserMixin):
    def __init__(self, id):
        self.id = id

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

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
            user = User(id=1)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login gagal. Periksa kembali username dan password Anda.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def get_active_users_count():
    # Menghitung jumlah dokumen di koleksi `user_pairs`
    return db.user_pairs.count_documents({})  # Menghitung semua dokumen di koleksi `user_pairs`

def get_total_users_count():
    # Menghitung jumlah dokumen di koleksi `users` untuk mendapatkan total pengguna
    return db.users.count_documents({})  # Menghitung semua dokumen di koleksi `users`

@app.route('/')
@login_required
def dashboard():
    active_users_count = get_active_users_count()
    total_users_count = get_total_users_count()
    
    return render_template('dashboard.html', 
                           active_users_count=active_users_count, 
                           total_users_count=total_users_count)

@app.route('/users')
@login_required
def users():
    user_id = request.args.get('user_id', '')
    username = request.args.get('username', '')
    gender = request.args.get('gender', '')
    city = request.args.get('city', '')
    age = request.args.get('age', '')
    page = int(request.args.get('page', 1))
    per_page = 30

    query = {}
    if user_id:
        query['user_id'] = user_id
    if username:
        query['username'] = username
    if gender:
        query['gender'] = gender
    if city:
        query['city'] = city
    if age:
        query['age'] = age

    users = list(users_collection.find(query).skip((page - 1) * per_page).limit(per_page))
    total_users = users_collection.count_documents(query)
    total_pages = ceil(total_users / per_page)

    pagination = {
        'page': page,
        'total': total_users,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1,
        'next_num': page + 1
    }

    return render_template('users.html', users=users, pagination=pagination)

@app.route('/activeusers')
@login_required
def activeusers():
    user_id_filter = request.args.get('user_id', '')
    username_filter = request.args.get('username', '')
    first_name_filter = request.args.get('first_name', '')
    full_name_filter = request.args.get('full_name', '')
    page = int(request.args.get('page', 1))
    per_page = 30

    # Query untuk user_pairs
    query = {}
    if user_id_filter:
        query['user_id'] = user_id_filter

    # Ambil data dari koleksi user_pairs
    active_user_ids = [user['user_id'] for user in user_pairs_collection.find(query)]

    # Query untuk users
    users_query = {}
    if username_filter:
        users_query['username'] = {'$regex': username_filter, '$options': 'i'}
    if first_name_filter:
        users_query['first_name'] = {'$regex': first_name_filter, '$options': 'i'}
    if full_name_filter:
        users_query['full_name'] = {'$regex': full_name_filter, '$options': 'i'}
    if active_user_ids:
        users_query['user_id'] = {'$in': active_user_ids}

    # Ambil data pengguna dari koleksi users
    total_users = users_collection.count_documents(users_query)
    total_pages = ceil(total_users / per_page)
    skip = (page - 1) * per_page

    active_users = list(users_collection.find(users_query).skip(skip).limit(per_page))

    pagination = {
        'page': page,
        'total': total_users,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1,
        'next_num': page + 1
    }

    return render_template(
        'activeusers.html',
        active_users=active_users,
        pagination=pagination
    )

@app.route('/chatrooms')
@login_required
def chatrooms():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'message_count')
    order = request.args.get('order', 'desc')

    per_page = 30
    
    sort_order = -1 if order == 'desc' else 1

    # Menghitung jumlah pesan dan mendapatkan timestamp terakhir berdasarkan chatroom_id
    pipeline = [
        {
            '$unwind': '$messages'
        },
        {
            '$group': {
                '_id': '$chatroom_id',
                'message_count': {'$sum': 1},
                'last_update': {'$max': '$messages.timestamp'}
            }
        },
        {
            '$sort': {sort_by: sort_order}
        },
        {
            '$skip': (page - 1) * per_page
        },
        {
            '$limit': per_page
        }
    ]
    
    chatrooms = list(chats_collection.aggregate(pipeline))

    # Konversi last_update dari string ke format tanggal
    for chatroom in chatrooms:
        if isinstance(chatroom['last_update'], str):
            chatroom['last_update'] = datetime.strptime(chatroom['last_update'], '%Y-%m-%d %H:%M:%S.%f').date()
    
    # Menghitung total chatroom untuk paginasi
    total_chatrooms_pipeline = [
        {
            '$unwind': '$messages'
        },
        {
            '$group': {
                '_id': '$chatroom_id'
            }
        },
        {
            '$count': 'total'
        }
    ]
    total_chatrooms_result = list(chats_collection.aggregate(total_chatrooms_pipeline))
    total_chatrooms = int(total_chatrooms_result[0]['total']) if total_chatrooms_result else 0
    total_pages = (total_chatrooms + per_page - 1) // per_page
    
    return render_template('chatrooms.html', chatrooms=chatrooms, page=page, total_pages=total_pages, sort_by=sort_by, order=order)

# Rute lainnya...

@app.template_filter('dateformat')
def dateformat(value, format='%Y-%m-%d'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            # Coba mengonversi string ke objek datetime
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Jika gagal mengonversi, anggap string sudah dalam format yang benar
            pass
    if isinstance(value, datetime):
        return value.strftime(format)
    return value  # Jika bukan objek datetime, kembalikan nilai asli

@app.route('/chats')
@login_required
def chats():
    chatroom_id = request.args.get('chatroom_id', '')
    timestamp = request.args.get('timestamp', '')

    query = {}
    if chatroom_id:
        query['chatroom_id'] = chatroom_id
    if timestamp:
        query['messages.timestamp'] = timestamp

    chats = []
    if query:
        chats_data = chats_collection.find(query)
        for chat in chats_data:
            for message in chat.get('messages', []):
                if message.get('message_type') in ['text', 'sticker', 'animation', 'document', 'photo', 'video', 'voice']:
                    if message.get('message_type') == 'photo':
                        file_id = message.get('message')
                        try:
                            message['message'] = get_telegram_file_url(HELLOTEMAN_BOT_TOKEN, file_id)
                        except Exception as e:
                            message['message'] = None
                            print(f"Error fetching photo URL: {e}")
                    chats.append({
                        'sender_id': message.get('sender_id'),
                        'message_type': message.get('message_type'),
                        'message': message.get('message')
                    })

    return render_template('chats.html', chats=chats)

@app.route('/view_photos')
@login_required
def view_photos():
    page = int(request.args.get('page', 1))
    per_page = 10
    bot_token = HELLOTEMAN_BOT_TOKEN

    chats = chats_collection.find({ "messages.message_type": "photo" })
    photos = []
    for chat in chats:
        for message in chat.get('messages', []):
            if message.get('message_type') == 'photo':
                sender_id = message.get('sender_id')
                chatroom_id = chat.get('chatroom_id')
                file_id = message.get('message')
                timestamp = message.get('timestamp')

                if not file_id:
                    continue

                try:
                    photo_url = get_telegram_file_url(bot_token, file_id)
                except Exception as e:
                    photo_url = None
                    print(f"Error fetching photo URL: {e}")

                photos.append({
                    'chatroom_id': chatroom_id,
                    'sender_id': sender_id,
                    'photo_url': photo_url,
                    'timestamp': timestamp
                })
                
     # Urutkan foto berdasarkan timestamp dari yang terbaru ke yang terlama
    photos = sorted(photos, key=lambda x: x['timestamp'], reverse=True)

    # Paginasi
    total_photos = len(photos)
    total_pages = ceil(total_photos / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    photos_paginated = photos[start:end]

    pagination = {
        'page': page,
        'total': total_photos,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1,
        'next_num': page + 1
    }

    return render_template('view_photo.html', photos=photos_paginated, pagination=pagination)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
