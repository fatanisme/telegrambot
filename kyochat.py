from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from pymongo import MongoClient
from bottokens import KYOCHAT_BOT_TOKEN

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['telegram_bot']
users_collection = db['users']
active_chats_collection = db['active_chats']
waiting_users_collection = db['waiting_users']

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_collection.update_one(
        {'user_id': user.id},
        {'$set': {'user_id': user.id, 'username': user.username, 'first_name': user.first_name, 'last_name': user.last_name}},
        upsert=True
    )
    await update.message.reply_text("Welcome! Use /settings to set your preferences.")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Gender", callback_data='gender')],
        [InlineKeyboardButton("Age", callback_data='age')],
        [InlineKeyboardButton("City", callback_data='city')],
        [InlineKeyboardButton("Language", callback_data='language')],
        [InlineKeyboardButton("Back", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

async def handle_settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'gender':
        keyboard = [
            [InlineKeyboardButton("Male", callback_data='gender_male')],
            [InlineKeyboardButton("Female", callback_data='gender_female')],
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Select your gender:", reply_markup=reply_markup)
    elif query.data == 'age':
        await query.edit_message_text(text="Please enter your age (1-99):")
        return
    elif query.data == 'city':
        await query.edit_message_text(text="Please enter your city:")
        return
    elif query.data == 'language':
        keyboard = [
            [InlineKeyboardButton("English", callback_data='language_english')],
            [InlineKeyboardButton("Indonesian", callback_data='language_indonesian')],
            [InlineKeyboardButton("Italian", callback_data='language_italian')],
            [InlineKeyboardButton("Spanish", callback_data='language_spanish')],
            [InlineKeyboardButton("Turkish", callback_data='language_turkish')],
            [InlineKeyboardButton("Korean", callback_data='language_korean')],
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Select your language:", reply_markup=reply_markup)
    elif query.data == 'back':
        await settings(update, context)

async def handle_settings_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if 'age' in context.user_data:
        age = update.message.text
        if age.isdigit() and 1 <= int(age) <= 99:
            users_collection.update_one(
                {'user_id': user.id},
                {'$set': {'age': int(age)}}
            )
            await update.message.reply_text("Age updated successfully!")
        else:
            await update.message.reply_text("Please enter a valid age between 1 and 99.")
        del context.user_data['age']
    elif 'city' in context.user_data:
        city = update.message.text
        users_collection.update_one(
            {'user_id': user.id},
            {'$set': {'city': city}}
        )
        await update.message.reply_text("City updated successfully!")
        del context.user_data['city']
    else:
        await update.message.reply_text("Invalid input. Please use /settings to update your preferences.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat = active_chats_collection.find_one({"user_id": user_id})

    if chat:
        partner_id = chat["partner_id"]
        message = update.message

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
            await context.bot.send_photo(chat_id=partner_id, photo=message.photo.file_id)
        elif message.forward_from:
            await context.bot.forward_message(chat_id=partner_id, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        else:
            pass

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'gender_male' or data == 'gender_female':
        users_collection.update_one(
            {'user_id': query.from_user.id},
            {'$set': {'gender': 'Male' if data == 'gender_male' else 'Female'}}
        )
        await query.edit_message_text(text="Gender updated successfully!")
    elif data.startswith('language_'):
        language = data.split('_')[1]
        users_collection.update_one(
            {'user_id': query.from_user.id},
            {'$set': {'language': language}}
        )
        await query.edit_message_text(text=f"Language set to {language.capitalize()}!")
    elif data == 'back':
        await settings(update, context)

async def handle_user_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    active_chat = active_chats_collection.find_one({"$or": [{"user_id": user_id}, {"partner_id": user_id}]})
    if active_chat:
        partner_id = active_chat["partner_id"] if active_chat["user_id"] == user_id else active_chat["user_id"]
        await context.bot.send_message(
            chat_id=partner_id,
            text="Your partner has left the chat. Use /join to find a new partner."
        )
        active_chats_collection.delete_one({"_id": active_chat["_id"]})

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    waiting_users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'user_id': user_id}},
        upsert=True
    )
    available_user = waiting_users_collection.find_one({'user_id': {'$ne': user_id}})
    if available_user:
        partner_id = available_user['user_id']
        active_chats_collection.insert_one({
            'user_id': user_id,
            'partner_id': partner_id,
            'chatroom_id': f"{user_id}{partner_id}"
        })
        active_chats_collection.insert_one({
            'user_id': partner_id,
            'partner_id': user_id,
            'chatroom_id': f"{partner_id}{user_id}"
        })
        waiting_users_collection.delete_many({'user_id': {'$in': [user_id, partner_id]}})
        await context.bot.send_message(chat_id=user_id, text="You are now connected with a partner.")
        await context.bot.send_message(chat_id=partner_id, text="You are now connected with a partner.")
    else:
        await update.message.reply_text("Waiting for a partner. Please wait...")

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member
    if chat_member.new_chat_member.status == 'left_chat_member':
        await handle_user_left(update, context)

def main():
    application = Application.builder().token(KYOCHAT_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_settings_choice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_input))
    application.add_handler(ChatMemberHandler(handle_chat_member_update))

    application.run_polling()

if __name__ == '__main__':
    main()
