from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from bottokens import KYOCHAT_BOT_TOKEN
import pymongo
from datetime import datetime
import re

# Setup MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["anonymous_chat_db"]
users_collection = db["users"]
waiting_users = db["waiting_users"]
active_chats = db["active_chats"]

# Command /start to register user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = {
        "user_id": str(update.message.chat_id),
        "username": update.message.from_user.username,
        "first_name": update.message.from_user.first_name,
        "last_name": update.message.from_user.last_name
    }
    users_collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)
    await update.message.reply_text("Welcome to Anonymous Chat! Your data has been saved. Use /join to find a chat partner or /settings to configure your preferences.")

# Command /settings to display settings menu
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Gender", callback_data='set_gender')],
        [InlineKeyboardButton("Age", callback_data='set_age')],
        [InlineKeyboardButton("City", callback_data='set_city')],
        [InlineKeyboardButton("Language", callback_data='set_language')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a setting to update:", reply_markup=reply_markup)

# Callback function for /settings options
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'set_gender':
        keyboard = [
            [InlineKeyboardButton("Male", callback_data='gender_male')],
            [InlineKeyboardButton("Female", callback_data='gender_female')],
            [InlineKeyboardButton("⬅️ Back", callback_data='back_to_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose your gender:", reply_markup=reply_markup)

    elif query.data == 'set_age':
        await query.edit_message_text(text="Please enter your age (1-99):", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data='back_to_settings')]
        ]))
        context.user_data['setting'] = 'age'

    elif query.data == 'set_city':
        await query.edit_message_text(text="Please enter your city:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data='back_to_settings')]
        ]))
        context.user_data['setting'] = 'city'

    elif query.data == 'set_language':
        keyboard = [
            [InlineKeyboardButton("English", callback_data='language_english')],
            [InlineKeyboardButton("Indonesian", callback_data='language_indonesian')],
            [InlineKeyboardButton("Italian", callback_data='language_italian')],
            [InlineKeyboardButton("Spanish", callback_data='language_spanish')],
            [InlineKeyboardButton("Turkish", callback_data='language_turkish')],
            [InlineKeyboardButton("Korean", callback_data='language_korean')],
            [InlineKeyboardButton("⬅️ Back", callback_data='back_to_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose your language:", reply_markup=reply_markup)

    elif query.data == 'back_to_settings':
        await settings(update, context)

    elif query.data.startswith('gender_'):
        gender = query.data.split('_')[1]
        users_collection.update_one({"user_id": str(query.message.chat_id)}, {"$set": {"gender": gender}})
        await query.edit_message_text(text=f"Gender set to {gender}.", reply_markup=None)

    elif query.data.startswith('language_'):
        language = query.data.split('_')[1]
        users_collection.update_one({"user_id": str(query.message.chat_id)}, {"$set": {"language": language}})
        await query.edit_message_text(text=f"Language set to {language}.", reply_markup=None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'setting' in context.user_data:
        user_id = str(update.message.chat_id)
        setting = context.user_data.pop('setting')

        if setting == 'age':
            if re.match(r'^\d+$', update.message.text) and 1 <= int(update.message.text) <= 99:
                users_collection.update_one({"user_id": user_id}, {"$set": {"age": int(update.message.text)}})
                await update.message.reply_text(f"Age set to {update.message.text}.", reply_markup=ReplyKeyboardRemove())
                await settings(update, context)
            else:
                await update.message.reply_text("Please enter a valid age between 1 and 99.")
        
        elif setting == 'city':
            users_collection.update_one({"user_id": user_id}, {"$set": {"city": update.message.text}})
            await update.message.reply_text(f"City set to {update.message.text}.", reply_markup=ReplyKeyboardRemove())
            await settings(update, context)
        return

    user_id = str(update.message.chat_id)
    chat = active_chats.find_one({"user_id": user_id})

    if chat:
        partner_id = chat["partner_id"]
        message = update.message

        # Save message to chat history in MongoDB
        active_chats.update_one(
            {"user_id": user_id},
            {"$push": {
                "messages": {
                    "sender_id": user_id,
                    "message_type": message.content_type,
                    "message": message.to_dict(),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                }
            }}
        )

        # Forward the message to the partner
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
        elif message.forward_from:
            await context.bot.send_message(chat_id=partner_id, text=f"Forwarded message:\n{message.text}")
        # Add handling for other message types if needed

# Anonymous Chat functions
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat_id)

    if waiting_users.count_documents({}) > 0:
        partner_id = waiting_users.find_one()["user_id"]
        waiting_users.delete_one({"user_id": partner_id})

        chatroom_id = user_id + partner_id
        active_chats.insert_one({"user_id": user_id, "partner_id": partner_id, "chatroom_id": chatroom_id, "messages": []})

        await context.bot.send_message(chat_id=user_id, text="You have been connected to a chat partner!")
        await context.bot.send_message(chat_id=partner_id, text="You have been connected to a chat partner!")
    else:
        waiting_users.insert_one({"user_id": user_id})
        await update.message.reply_text("Waiting for a chat partner...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat_id)
    chat = active_chats.find_one({"user_id": user_id})

    if chat:
        partner_id = chat["partner_id"]
        active_chats.delete_one({"user_id": user_id})

        await context.bot.send_message(chat_id=partner_id, text="Your partner has left the chat. Use /join to find a new partner.")
        await update.message.reply_text("You have left the chat.")
    else:
        waiting_users.delete_one({"user_id": user_id})
        await update.message.reply_text("You have been removed from the waiting list.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command.")

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(KYOCHAT_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT | filters.STICKER | filters.ANIMATION | filters.VOICE | filters.VIDEO | filters.DOCUMENT, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
