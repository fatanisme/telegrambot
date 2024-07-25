from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes, CallbackContext
from pymongo import MongoClient
from bottokens import HELLOTEMAN_BOT_TOKEN
from datetime import datetime
import random

# Inisialisasi koneksi ke MongoDB
mongo_client = MongoClient('localhost', 27017)
db = mongo_client['helloteman_db']
users_collection = db['users']
chats_collection = db['chats']
khodam_collection = db['khodam']
jodoh_collection = db['couples']
pairs_collection = db["user_pairs"]

# Fungsi untuk menyimpan chat ke MongoDB
def save_chat_to_mongodb(user_id, partner_id, message_type, message):
    chat_data = {
        "user_id": user_id,
        "partner_id": partner_id,
        "chatroom_id": str(user_id) + str(partner_id),
        "messages": [
            {
                "sender_id": user_id,
                "message_type": message_type,
                "message": message,
                "timestamp": datetime.now()
            }
        ]
    }
    if not chats_collection.find_one({'$or': [{'$and': [{'user_id': user_id}, {'partner_id': partner_id}]}, {'$and': [{'user_id': partner_id}, {'partner_id': user_id}]}]}):
        result = chats_collection.insert_one(chat_data)
        print(f"Chat saved to MongoDB with ID: {result.inserted_id}")
    else:
        result = chats_collection.update_one({'$or': [{'$and': [{'user_id': user_id}, {'partner_id': partner_id}]}, {'$and': [{'user_id': partner_id}, {'partner_id': user_id}]}]}, {'$push': {'messages': {'sender_id': user_id, 'message_type': message_type, 'message': message, 'timestamp': datetime.now()}}})
        print(f"Chat updated in MongoDB with ID: {result.matched_count}")

# Fungsi untuk menyimpan pengguna ke MongoDB
def save_user_to_mongodb(user_id, **kwargs):
    try:
        user = users_collection.find_one({"user_id": user_id})
        if user:
            update_fields = {}
            for key, value in kwargs.items():
                if value is not None:
                    update_fields[key] = value
            if update_fields:
                users_collection.update_one({"user_id": user_id}, {"$set": update_fields})
                print("User updated in the database.")
        else:
            # Jika pengguna tidak ditemukan, buat dokumen pengguna baru
            user_data = {"user_id": user_id}
            for key, value in kwargs.items():
                if value is not None:
                    user_data[key] = value
            result = users_collection.insert_one(user_data)
            print(f"User inserted into the database with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error saving user to database: {e}")

            
# Daftar untuk menyimpan user
users = []
user_settings = {}

user_pairs = {}

# Fungsi untuk memuat user_pairs dari MongoDB
def load_user_pairs_from_mongodb():
    data = pairs_collection.find_one({})
    if data:
        return data.get("user_pairs", {})
    return {}

# Fungsi untuk menyimpan user_pairs ke MongoDB
def save_user_pairs_to_mongodb(user_pairs):
    pairs_collection.update_one({}, {"$set": {"user_pairs": user_pairs}}, upsert=True)

# Fungsi untuk menghapus pasangan pengguna dari MongoDB
def remove_user_pair(user_id):
    data = pairs_collection.find_one({})
    if data:
        user_pairs = data.get("user_pairs", {})
        if user_id in user_pairs:
            del user_pairs[user_id]
            save_user_pairs_to_mongodb(user_pairs)

# Fungsi untuk memuat user_pairs ketika bot dimulai
def on_startup():
    global user_pairs
    user_pairs = load_user_pairs_from_mongodb()
    
async def main_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("👽👽👽 CEK KHODAM 👽👽👽", callback_data='check_khodam')],
        [InlineKeyboardButton("💗💗💗 CEK JODOH 💗💗💗", callback_data='check_jodoh')],
        [InlineKeyboardButton("Batal", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Pilih opsi:', reply_markup=reply_markup)

async def main_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'check_khodam':
        user_settings[user_id] = 'waiting_for_khodam_name'
        await query.edit_message_text("Silakan masukkan nama Anda untuk mendapatkan Khodam:")        
    elif query.data == 'check_jodoh':
        user_settings[user_id] = 'waiting_for_couple'
        keyboard = [
                [InlineKeyboardButton("👽👽👽 PRIA 👽👽👽", callback_data='pria')],
                [InlineKeyboardButton("💗💗💗 WANITA 💗💗💗", callback_data='wanita')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Pilih Jenis Kelamin Anda :', reply_markup=reply_markup)
    elif query.data == 'cancel':
        await query.edit_message_text('Operasi dibatalkan.')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    full_name = user.full_name
    save_user_to_mongodb(user_id, username=username, first_name=first_name, last_name=last_name, full_name=full_name)
    
    start_message = (
        "Selamat datang di Anonymous Chat!\n\n"
        "Coba perintah berikut untuk memastikan bot berfungsi:\n"
        "/bermain - Untuk mengecek khodam dan jodoh yang kamu miliki.\n"
        "/join - Untuk bergabung ke dalam pool chat dan langsung memulai chat dengan pengguna acak.\n"
        "/leave - Untuk keluar dari pool chat dan mengakhiri obrolan saat ini.\n"
        "/help - Memulai bot dan menerima pesan sambutan.\n"
        "/settings - Update data diri anda (Umur, Jenis kelamin, Alamat).\n"
    )
    await update.message.reply_text(start_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    full_name = user.full_name
    save_user_to_mongodb(user_id, username=username, first_name=first_name, last_name=last_name, full_name=full_name)
    
    help_message = (
        "Daftar perintah yang tersedia:\n\n"
        "/bermain - Untuk mengecek khodam dan jodoh yang kamu miliki.\n"
        "/join - Bergabung ke dalam pool chat untuk memulai chat dengan pengguna acak.\n"
        "/leave - Keluar dari pool chat dan mengakhiri obrolan saat ini.\n"
        "/help - Memulai bot dan menerima pesan sambutan.\n"
        "/settings - Update data diri anda (Umur, Jenis kelamin, Alamat).\n"
    )
    await update.message.reply_text(help_message)

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    full_name = user.full_name
    save_user_to_mongodb(user_id, username=username, first_name=first_name, last_name=last_name, full_name=full_name)
    
    if user.id not in [u.id for u in users]:
        users.append(user)
        await update.message.reply_text('Anda telah bergabung ke dalam pool chat random. Sedang mencari pasangan chat.')
        await start_chat(update, context, user.id)
    else:
        await update.message.reply_text('Anda sudah berada di dalam pool chat. Gunakan /leave terlebih dahulu untuk keluar dari obrolan.')

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    other_users = [u.id for u in users if u.id != user_id and u.id not in user_pairs.values()]
    if other_users:
        partner_id = random.choice(other_users)
        user_pairs[user_id] = partner_id
        user_pairs[partner_id] = user_id
        await context.bot.send_message(chat_id=partner_id, text=f"Anda terhubung dengan pasangan anda. Mulailah mengobrol!")
        await context.bot.send_message(chat_id=user_id, text=f"Anda terhubung dengan pasangan anda. Mulailah mengobrol!")
    else:
        await context.bot.send_message(chat_id=user_id, text='Harap Tunggu Sebentar....')

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in user_pairs:
        remove_user_pair_from_mongodb(user_id)
        await context.bot.send_message(chat_id=user_id, text="Anda telah meninggalkan chat. Pasangan Anda juga telah diberitahu.")
        partner_id = user_pairs.get(user_id)
        if partner_id:
            await context.bot.send_message(chat_id=partner_id, text="Pasangan Anda telah meninggalkan chat.")
    else:
        await context.bot.send_message(chat_id=user_id, text="Anda tidak sedang dalam chat dengan pasangan.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    if user.id in [u.id for u in users]:
        await update.message.reply_text('Anda sudah berada di dalam pool chat. Gunakan /leave terlebih dahulu untuk memulai obrolan baru.')
    else:
        await update.message.reply_text('Anda belum bergabung dalam pool chat. Gunakan /join untuk bergabung.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_input = update.message.text    
    partner_id = user_pairs.get(user.id)

    
    if partner_id:
        if update.message.text:
            await context.bot.send_message(chat_id=partner_id, text=update.message.text)
            save_chat_to_mongodb(str(user.id), str(partner_id), "text", update.message.text)
        elif update.message.sticker:
            await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "sticker", update.message.sticker.file_id)
        elif update.message.animation:
            await context.bot.send_animation(chat_id=partner_id, animation=update.message.animation.file_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "animation", update.message.animation.file_id)
        elif update.message.document:
            await context.bot.send_document(chat_id=partner_id, document=update.message.document.file_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "document", update.message.document.file_id)
        elif update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(chat_id=partner_id, photo=photo_file_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "photo", photo_file_id)
        elif update.message.video:
            await context.bot.send_video(chat_id=partner_id, video=update.message.video.file_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "video", update.message.video.file_id)
        elif update.message.voice:
            await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "voice", update.message.voice.file_id)
        elif update.message.poll:
            poll = update.message.poll
            await context.bot.send_poll(chat_id=partner_id, question=poll.question, options=[opt.text for opt in poll.options], is_anonymous=poll.is_anonymous, type=poll.type, allows_multiple_answers=poll.allows_multiple_answers, correct_option_id=poll.correct_option_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "poll", {"question": poll.question, "options": [opt.text for opt in poll.options], "is_anonymous": poll.is_anonymous, "type": poll.type, "allows_multiple_answers": poll.allows_multiple_answers, "correct_option_id": poll.correct_option_id})
        elif update.message.forward_from or update.message.forward_from_chat:
            await context.bot.forward_message(chat_id=partner_id, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
            save_chat_to_mongodb(str(user.id), str(partner_id), "forward", {"from_chat_id": update.message.chat_id, "message_id": update.message.message_id})
    elif user.id in user_settings:
        if user_settings[user.id] == 'waiting_for_age':
            if user_input.isdigit():
                save_user_to_mongodb(user.id, age=user_input)
                await update.message.reply_text(f"Umur Anda telah diperbarui menjadi {user_input}.")
                await settings(update, context)  # Kembali ke daftar pengaturan
            else:
                await update.message.reply_text("Harap masukkan umur yang valid.")
        elif user_settings[user.id] == 'waiting_for_gender':
            if user_input.lower() in ['pria', 'wanita']:
                save_user_to_mongodb(user.id, gender=user_input.capitalize())
                await update.message.reply_text(f"Jenis kelamin Anda telah diperbarui menjadi {user_input}.")
                await settings(update, context)  # Kembali ke daftar pengaturan
            else:
                await update.message.reply_text("Harap pilih jenis kelamin yang valid: 'Pria' atau 'Wanita'.")
        elif user_settings[user.id] == 'waiting_for_city':
            save_user_to_mongodb(user.id, city=user_input)
            await update.message.reply_text(f"Kota/Kabupaten Anda telah diperbarui menjadi {user_input}.")
            await settings(update, context)  # Kembali ke daftar pengaturan
        elif user_settings[user.id] == 'waiting_for_khodam_name':
            # Mengambil Khodam secara random dari collection
            khodam_list = list(khodam_collection.find())
            
            if random.random() < 0.5:
                message = await update.message.reply_text("Memilih Khodam...")
                # Menampilkan rolling list selama 4 detik
                num_rolls = 10  # Total list Khodam yang ditampilkan
                for i in range(num_rolls):
                    random_khodam = random.choice(khodam_list)
                    khodam_name = random_khodam.get('name', 'Khodam tidak diketahui')
                    await message.edit_text(f"{khodam_name}  (Roll {i+1})")

                await message.edit_text("Khodam Anda sepertinya sedang berlibur dan tidak ingin diganggu. Mungkin dia sedang merenungkan betapa sulitnya hidup dengan ‘keistimewaan’ Anda. Cobalah lagi nanti, mungkin dia kembali!\n"
                                        "Just Kidding !!! Yuk coba lagii 😊")
                await main_command(update, context)  # Kembali ke daftar /bermain
            else:
                if khodam_list:
                    # Mengirim pesan awal yang menunjukkan sistem sedang memilih Khodam
                    message = await update.message.reply_text("Memilih Khodam...")

                    # Menampilkan rolling list selama 4 detik
                    num_rolls = 10  # Total list Khodam yang ditampilkan
                    for i in range(num_rolls):
                        random_khodam = random.choice(khodam_list)
                        khodam_name = random_khodam.get('name', 'Khodam tidak diketahui')
                        await message.edit_text(f"{khodam_name}  (Roll {i+1})")

                    # Pilih Khodam secara final
                    final_khodam = random.choice(khodam_list)
                    final_khodam_name = final_khodam.get('name', 'Khodam tidak diketahui')

                    # Edit pesan dengan hasil akhir
                    await message.edit_text(f"Halo {user_input}, Khodam Anda adalah: {final_khodam_name}")

                else:
                    await update.message.reply_text("Maaf, tidak ada Khodam yang tersedia saat ini.")
        elif user_settings[user.id] == 'waiting_for_pria' or user_settings[user.id] == 'waiting_for_wanita':
                            
            if user_settings[user.id] == 'waiting_for_pria':
                user_gender = "pria"
                jodoh_list = list(jodoh_collection.find({'gender': 'wanita'}))
                
            elif user_settings[user.id] == 'waiting_for_wanita':
                user_gender = "wanita"
                jodoh_list = list(jodoh_collection.find({'gender': 'pria'}))
            
            if jodoh_list:
                
                # Mengirim pesan awal yang menunjukkan sistem sedang memilih Khodam
                message = await update.message.reply_text("Memilih Jodoh...")

                # Menampilkan rolling list selama 4 detik
                num_rolls = 10  # Total list Khodam yang ditampilkan
                for i in range(num_rolls):
                    random_jodoh = random.choice(jodoh_list)
                    jodoh_name = random_jodoh.get('name', 'Jodoh tidak diketahui')
                    await message.edit_text(f"{jodoh_name}  (Roll {i+1})")

                # Pilih Khodam secara final
                final_jodoh = random.choice(jodoh_list)
                final_jodoh_name = final_jodoh.get('name', 'Jodoh tidak diketahui')

                # Edit pesan dengan hasil akhir
                await message.edit_text(f"Halo {user_input}, Jodoh Anda adalah: {final_jodoh_name}")
                save_user_to_mongodb(user.id, gender=user_gender.capitalize())
            else:
                await update.message.reply_text("Maaf, tidak ada Jodoh yang tersedia saat ini.")
                            
        # Menghapus state
        user_settings.pop(user.id, None)

    else:
        await update.message.reply_text(
            'Anda tidak sedang dalam chat dengan siapapun.\n\n'
            "Gunakan /join untuk bergabung ke dalam pool chat dan langsung memulai chat dengan pengguna acak.\n"
        )

async def active_users(update: Update,context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = pairs_collection.find_one({})
        
        if data:
            user_pairs = data.get("user_pairs", {})
            active_user_count = len(user_pairs)
            
            if active_user_count == 0:
                await update.message.reply_text("Tidak ada pengguna aktif saat ini.")
                return

            # Mengumpulkan ID pengguna dan nama lengkap dari daftar pengguna aktif
            active_user_info = [f"ID: {user_id}"]
            active_user_list = "\n".join(active_user_info)

            # Mengirimkan jumlah pengguna aktif dan daftar pengguna aktif
            response_message = (
                f"Jumlah pengguna aktif saat ini: {active_user_count}\n\n"
                f"Daftar pengguna aktif:\n{active_user_list}"
            )
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text("Tidak ada data pasangan pengguna ditemukan di database.")
    
    except Exception as e:
        
        await update.message.reply_text("Terjadi kesalahan saat mengambil data pengguna aktif.")
        
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = " ".join(context.args)
    if message:
        all_users = [user['user_id'] for user in users_collection.find()]
        for user_id in all_users:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
        await update.message.reply_text(f"Pesan '{message}' telah diposting kepada {len(all_users)} pengguna.")
    else:
        await update.message.reply_text("Harap masukkan pesan yang ingin diposting. Contoh: /post ini adalah pesan yang akan dipost.")

async def count_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_count = users_collection.count_documents({})
    await update.message.reply_text(f"Jumlah pengguna yang ada di database: {user_count}")

async def userdetail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = context.args[0] if context.args else None
    if user_id and user_id.isdigit():
        user = users_collection.find_one({"user_id": int(user_id)})
        if user:
            user_info = (
                f"ID: {user.get('user_id')}\n"
                f"Username: @{user.get('username', 'N/A')}\n"
                f"First Name: {user.get('first_name', 'N/A')}\n"
                f"Last Name: {user.get('last_name', 'N/A')}\n"
                f"Full Name: {user.get('full_name', 'N/A')}\n"
                f"Age: {user.get('age', 'N/A')}\n"
                f"Gender: {user.get('gender', 'N/A')}\n"
                f"City: {user.get('city', 'N/A')}"
            )
            await update.message.reply_text(user_info)
        else:
            await update.message.reply_text(f"Pengguna dengan ID {user_id} tidak ditemukan.")
    else:
        await update.message.reply_text("Harap masukkan user_id yang valid. Contoh: /userdetail 1")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    keyboard = [
        [InlineKeyboardButton("Umur", callback_data='update_age')],
        [InlineKeyboardButton("Jenis Kelamin", callback_data='update_gender')],
        [InlineKeyboardButton("Kota/Kabupaten", callback_data='update_city')],
        [InlineKeyboardButton("Tutup", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Pilih pengaturan yang ingin diubah:', reply_markup=reply_markup)



async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'update_age':
        user_settings[user_id] = 'waiting_for_age'
        await query.edit_message_text('Silakan kirimkan umur Anda:')
    elif query.data == 'update_gender':
        user_settings[user_id] = 'waiting_for_gender'
        await query.edit_message_text('Silakan pilih jenis kelamin Anda dengan mengetikkan "Pria" atau "Wanita":')
    elif query.data == 'update_city':
        user_settings[user_id] = 'waiting_for_city'
        await query.edit_message_text('Silakan kirimkan nama kota atau kabupaten Anda:')
    elif query.data == 'close':
        await query.edit_message_text('Pengaturan ditutup.')

async def handle_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'pria':
        user_settings[user_id] = 'waiting_for_pria'
        await query.edit_message_text('Silakan masukan nama Anda:')
    elif query.data == 'wanita':
        user_settings[user_id] = 'waiting_for_wanita'
        await query.edit_message_text('Silakan masukan nama Anda:')

async def myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user = users_collection.find_one({"user_id": user_id})

    if user:
        user_info = (
            f"ID: {user.get('user_id')}\n"
            f"Username: @{user.get('username', 'N/A')}\n"
            f"First Name: {user.get('first_name', 'N/A')}\n"
            f"Last Name: {user.get('last_name', 'N/A')}\n"
            f"Full Name: {user.get('full_name', 'N/A')}\n"
            f"Age: {user.get('age', 'N/A')}\n"
            f"Gender: {user.get('gender', 'N/A')}\n"
            f"City: {user.get('city', 'N/A')}"
        )
        await update.message.reply_text(user_info)
    else:
        await update.message.reply_text("Profil Anda tidak ditemukan. Pastikan Anda telah bergabung dengan bot.")


def main():
    application = ApplicationBuilder().token(HELLOTEMAN_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("chat", chat))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CommandHandler("activeusers", active_users))
    application.add_handler(CommandHandler("post", post))
    application.add_handler(CommandHandler("countusers", count_users))
    application.add_handler(CommandHandler("userdetail", userdetail))
    application.add_handler(CommandHandler("settings", settings))
    
    application.add_handler(CommandHandler("bermain", main_command))  # Tambahkan baris ini
    application.add_handler(CallbackQueryHandler(main_button_handler, pattern='^(check_khodam|check_jodoh|cancel)$'))

    application.add_handler(CommandHandler("myprofile", myprofile))  # Tambahkan baris ini

    application.add_handler(CallbackQueryHandler(handle_message_callback))
    application.add_handler(CallbackQueryHandler(settings_button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    global user_pairs
    user_pairs = load_user_pairs_from_mongodb()
    
    application.run_polling()

if __name__ == '__main__':
    main()