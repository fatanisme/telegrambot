from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from pymongo import MongoClient
from bottokens import KYOCHAT_BOT_TOKEN

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['kyochat_db']
users_collection = db['users']
active_chats_collection = db['active_chats']
waiting_users_collection = db['waiting_users']
match_history_collection = db['match_history']

user_settings = {}

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user    
    users_collection.update_one(
        {'user_id': user.id},
        {'$set': {'user_id': user.id, 'username': user.username, 'first_name': user.first_name, 'last_name': user.last_name}},
        upsert=True
    )
    await keyboard_markup(update,context)

# Fungsi untuk menambahkan riwayat pasangan


async def keyboard_markup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    # Fetch user type from the database
    user = users_collection.find_one({'user_id': user_id})
    
    if user and user.get('user_type') == 'premium':
        keyboard = [
            [KeyboardButton("🔍 Find a Partner 🔍")],
            [KeyboardButton("👨 Find a Male 👨"), KeyboardButton("👩 Find a Female 👩")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🔍 Find a Partner 🔍")],
            [KeyboardButton("👨👩 Find by Gender 👨👩")]
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Use /join to find a new partner.",reply_markup=reply_markup)

async def remove_reply_keyboard_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
        # Memperbarui pesan dengan menghapus reply keyboard
        await update.message.reply_text(
            "Waiting for a partner ...",
            reply_markup=ReplyKeyboardRemove()
        )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("👤 Gender", callback_data='gender')],
        [InlineKeyboardButton("🎂 Age", callback_data='age')],
        [InlineKeyboardButton("🏙️ City", callback_data='city')],
        [InlineKeyboardButton("🌐 Language", callback_data='language')],
        [InlineKeyboardButton("❌ Close", callback_data='close')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Choose an option:", reply_markup=reply_markup)

async def handle_settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'gender':
        keyboard = [
            [InlineKeyboardButton("Male", callback_data='gender_male')],
            [InlineKeyboardButton("Female", callback_data='gender_female')],
            [InlineKeyboardButton("⬅️ Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select your gender:", reply_markup=reply_markup)
    elif query.data == 'age':
        user_settings[user_id] = 'waiting_for_age'
        await query.edit_message_text("Please enter your age (1-99):")
    elif query.data == 'city':
        user_settings[user_id] = 'waiting_for_city'
        await query.edit_message_text("Please enter your city:")
    elif query.data == 'language':
        user_settings[user_id] = 'waiting_for_language'
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='language_english')],
            [InlineKeyboardButton("🇮🇩 Indonesian", callback_data='language_indonesian')],
            [InlineKeyboardButton("🇮🇹 Italian", callback_data='language_italian')],
            [InlineKeyboardButton("🇪🇸 Spanish", callback_data='language_spanish')],
            [InlineKeyboardButton("🇹🇷 Turkish", callback_data='language_turkish')],
            [InlineKeyboardButton("🇰🇷 Korean", callback_data='language_korean')],
            [InlineKeyboardButton("⬅️ Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select your language:", reply_markup=reply_markup)
    elif query.data == 'close':
        await query.edit_message_text('Type /settings for change your appearance or Type /join for find a new partner !')
    elif query.data == 'back':
        await settings(update, context)
    elif query.data == 'gender_male' or query.data == 'gender_female':
            gender = 'Male' if query.data == 'gender_male' else 'Female'
            users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'gender': gender}}
            )
            await query.edit_message_text("Gender updated successfully!")
    elif user_settings.get(user_id) == 'waiting_for_language':
            language = query.data.split('_')[1]
            users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'language': language}}
            )
            await query.edit_message_text(f"Language set to {language.capitalize()}!")
            del user_settings[user_id]
    
    else:
        await query.edit_message_text("Invalid callback data or settings state.")
    
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat = active_chats_collection.find_one({"$or": [{"user_id": user_id}, {"partner_id": user_id}]})
    user = users_collection.find_one({'user_id': user_id})
    user_type = user.get('user_type') if user else None
    
    message = update.message
    
    if chat is None:
        if message.text == "🔍 Find a Partner 🔍":
            await join(update, context)
            
        elif message.text == "👨 Find a Male 👨":
            if user_type == 'premium':
                await join(update, context, gender='Male')
            else:
                await update.message.reply_text("This feature is available for premium users only.")
        elif message.text ==  "👩 Find a Female 👩":
            if user_type == 'premium':
                await join(update, context, gender='Female')
            else:
                await update.message.reply_text("This feature is available for premium users only.")
        elif message.text == "👨👩 Find by Gender 👨👩":
            if user_type == 'premium':
                await update.message.reply_text("Please specify the gender: Male or Female.")
            else:
                await update.message.reply_text("This feature is available for premium users only.")
        elif user_settings.get(user_id) == 'waiting_for_age':
            if message.text.isdigit() and 1 <= int(message.text) <= 99:
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'age': int(message.text)}}
                )
                await update.message.reply_text("Age updated successfully!")
            else:
                await update.message.reply_text("Please enter a valid age between 1 and 99.")
        elif user_settings.get(user_id) == 'waiting_for_city':
            users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'city': message.text}}
            )
            await update.message.reply_text("City updated successfully!")
        elif not chat:
            await update.message.reply_text("You are not in an active chat. Please use /join to find a partner.")
            return
    else:
        partner_id = chat['partner_id'] if chat['user_id'] == user_id else chat['user_id']
        
        if message.text:
            await context.bot.send_message(chat_id=partner_id, text=message.text)
        elif message.sticker:
            await context.bot.send_sticker(chat_id=partner_id, sticker=message.sticker.file_id)
        elif message.animation:
            await context.bot.send_animation(chat_id=partner_id, animation=message.animation.file_id)
        elif message.voice:
            await context.bot.send_voice(chat_id=partner_id, voice=message.voice.file_id)
        elif message.video:
            await context.bot.send_video(chat_id=partner_id, video=message.video.file_id)
        elif message.document:
            await context.bot.send_document(chat_id=partner_id, document=message.document.file_id)
        elif message.photo:
            # Handle photo which might be a tuple of sizes
            photo_file_id = message.photo[-1].file_id  # Get the highest resolution photo
            await context.bot.send_photo(chat_id=partner_id, photo=photo_file_id)
        elif message.forward_from:
            await context.bot.forward_message(chat_id=partner_id, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        else:
            pass

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat = active_chats_collection.find_one({"$or": [{"user_id": user_id}, {"partner_id": user_id}]})
    
    if not chat:
        await update.message.reply_text("You are not in an active chat.")
        return

    partner_id = chat['partner_id'] if chat['user_id'] == user_id else chat['user_id']
    
    # Remove chat from active_chats
    active_chats_collection.delete_one({"_id": chat['_id']})
    
    # Notify both users
    await context.bot.send_message(chat_id=user_id, text="You have left the chat.")
    await context.bot.send_message(chat_id=partner_id, text="Your chat partner has left the chat. Use /join to find a new partner.")
    
    await keyboard_markup(update,context) 

    # Remove the user from active_chats
    active_chats_collection.delete_many({"$or": [{"user_id": user_id}, {"partner_id": user_id}]})
    
    waiting_users_collection.delete_one({"user_id": user_id})
    waiting_users_collection.delete_one({"user_id": partner_id})

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE, gender=None):
    user_id = update.message.from_user.id
    # Ambil data pengguna dari database
    user_data = users_collection.find_one({'user_id': user_id})
    # Tentukan bahasa pengguna atau set ke English jika belum ada
    user_language = user_data.get('language', 'English')
    
    # Check if user is already in an active chat
    if active_chats_collection.find_one({"$or": [{"user_id": user_id}, {"partner_id": user_id}]}):
        await update.message.reply_text("You are already in an active chat. Use /leave to exit the current chat before joining a new one.")
        return

    # Check if the user is already waiting
    existing_user = waiting_users_collection.find_one({"user_id": user_id})
    if existing_user:
        await update.message.reply_text("You are already waiting for a partner.")
        return
    
    # Find a partner from waiting_users
    query = {"status": "waiting", "language": user_language}
    if gender:
        query["gender"] = gender
    else:
        query["gender"] = {"$nin": [None,"Unknown","Male","Female"]}
        
    partner = waiting_users_collection.find_one(query)
    if partner:
        partner_id = partner['user_id']
        # Create a new chat
        chatroom_id = str(user_id) + str(partner_id)
        active_chats_collection.insert_one({
            "user_id": user_id,
            "partner_id": partner_id,
            "chatroom_id": chatroom_id,
            "messages": []
        })
        active_chats_collection.insert_one({
            "user_id": partner_id,
            "partner_id": user_id,
            "chatroom_id": chatroom_id,
            "messages": []
        })
        
        # Tambahkan ke riwayat pasangan
        
        # Notify both users
        await remove_reply_keyboard_from_message(update, context)
        await context.bot.send_message(chat_id=user_id, text=f"You have been matched with a new partner. Start chatting!")
        await context.bot.send_message(chat_id=partner_id, text=f"You have been matched with a new partner. Start chatting!")
        
        # Remove user from waiting_users collection
        waiting_users_collection.delete_one({"user_id": user_id})
        waiting_users_collection.delete_one({"user_id": partner_id})
    else:
        # Add user to waiting_users collection
        users_collection.update_one(
            {'user_id': user_id},
            {'$set': {'gender': 'Unknown', 'language': user_language}}  # Update gender as unknown or set properly if available
        )
        waiting_users_collection.insert_one({"user_id": user_id, "status": "waiting", "gender": gender, 'language': user_language})
        await update.message.reply_text(
            "You have been added to the waiting list. Please wait while we find a partner for you.",
            reply_markup= await remove_reply_keyboard_from_message(update, context)
        )
        
def main():
    application = Application.builder().token(KYOCHAT_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('leave', leave))
    application.add_handler(CommandHandler('join', join))
    
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handle_settings_choice))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
