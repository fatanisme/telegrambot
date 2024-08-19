from pymongo import MongoClient
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from bottokens import KYOCHAT_BOT_TOKEN
import logging

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['telegram_bot']
users_collection = db['users']
chats_collection = db['chats']
messages_collection = db['messages']


def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_collection.update_one({'user_id': user_id}, {'$set': {'user_id': user_id}}, upsert=True)
    
    keyboard = [['Find a Partner', 'Find by Gender']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Welcome to the anonymous chat bot! Choose an option:', reply_markup=reply_markup)

def join(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = users_collection.find_one({'user_id': user_id})

    if user:
        # Add user to chat pool
        # Implement logic for gender-based pairing if needed
        update.message.reply_text('You have been added to the chat pool. Please wait while we find a partner.')
    else:
        update.message.reply_text('Please start by using /start command.')

def leave(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat = chats_collection.find_one({'$or': [{'user1': user_id}, {'user2': user_id}]})

    if chat:
        partner_id = chat['user2'] if chat['user1'] == user_id else chat['user1']
        chats_collection.delete_one({'_id': chat['_id']})
        
        # Notify both users
        update.message.reply_text('You have left the chat. Please use /join to find a new chat partner.')
        context.bot.send_message(chat_id=partner_id, text='Your chat partner has left. Please use /join to find a new chat partner.')
        
        # Provide InlineKeyboard for feedback and reporting
        keyboard = [
            [InlineKeyboardButton('👍 Thumbs Up', callback_data='like'),
             InlineKeyboardButton('👎 Thumbs Down', callback_data='dislike')],
            [InlineKeyboardButton('Report', callback_data='report')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please provide feedback:', reply_markup=reply_markup)
    else:
        update.message.reply_text('You are not currently in a chat session.')

def next_chat(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat = chats_collection.find_one({'$or': [{'user1': user_id}, {'user2': user_id}]})

    if chat:
        partner_id = chat['user2'] if chat['user1'] == user_id else chat['user1']
        leave(update, context)
        context.bot.send_message(chat_id=partner_id, text='Your chat partner has left. Please use /join to find a new chat partner.')
    else:
        update.message.reply_text('You are not currently in a chat session.')

def settings(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton('Age', callback_data='set_age')],
        [InlineKeyboardButton('Gender', callback_data='set_gender')],
        [InlineKeyboardButton('City', callback_data='set_city')],
        [InlineKeyboardButton('Auto-Reconnect', callback_data='auto_reconnect')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a setting to update:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if data == 'set_age':
        query.edit_message_text(text="Please enter your age (1-99):")
        return

    if data == 'set_gender':
        keyboard = [
            [InlineKeyboardButton('Male', callback_data='gender_male')],
            [InlineKeyboardButton('Female', callback_data='gender_female')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Please select your gender:", reply_markup=reply_markup)
        return

    if data == 'gender_male' or data == 'gender_female':
        users_collection.update_one({'user_id': user_id}, {'$set': {'gender': 'male' if data == 'gender_male' else 'female'}})
        query.edit_message_text(text="Gender updated successfully!")
        return

    if data == 'set_city':
        query.edit_message_text(text="Please enter your city:")
        return

    if data == 'auto_reconnect':
        users_collection.update_one({'user_id': user_id}, {'$set': {'auto_reconnect': True}})
        query.edit_message_text(text="Auto-reconnect enabled.")
        return

    if data == 'report':
        keyboard = [
            [InlineKeyboardButton('Advertising', callback_data='report_advertising')],
            [InlineKeyboardButton('Selling', callback_data='report_selling')],
            [InlineKeyboardButton('Child Porn', callback_data='report_child_porn')],
            [InlineKeyboardButton('Begging', callback_data='report_begging')],
            [InlineKeyboardButton('Insulting', callback_data='report_insulting')],
            [InlineKeyboardButton('Violence', callback_data='report_violence')],
            [InlineKeyboardButton('Vulgar Partner', callback_data='report_vulgar')],
            [InlineKeyboardButton('Cancel', callback_data='report_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Select a reason for reporting:", reply_markup=reply_markup)
        return

    if data.startswith('report_'):
        # Handle reporting logic
        report_type = data.replace('report_', '')
        query.edit_message_text(text=f"Reported for {report_type}. Thank you for your feedback.")
        return

    if data == 'report_cancel':
        query.edit_message_text(text="Report cancelled.")

def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    message_type = 'text'
    content = update.message.text

    if update.message.photo:
        message_type = 'photo'
        content = update.message.photo[-1].file_id
    elif update.message.video:
        message_type = 'video'
        content = update.message.video.file_id
    elif update.message.voice:
        message_type = 'voice'
        content = update.message.voice.file_id
    elif update.message.document:
        message_type = 'document'
        content = update.message.document.file_id
    elif update.message.poll:
        message_type = 'poll'
        content = update.message.poll.to_dict()
    elif update.message.sticker:
        message_type = 'sticker'
        content = update.message.sticker.file_id
    elif update.message.animation:
        message_type = 'animation'
        content = update.message.animation.file_id

    # Save message to MongoDB
    message_data = {
        'user_id': user_id,
        'chat_id': chat_id,
        'message_id': update.message.message_id,
        'message_type': message_type,
        'content': content
    }
    messages_collection.insert_one(message_data)

def main():
    updater = Updater(KYOCHAT_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('join', join))
    dp.add_handler(CommandHandler('leave', leave))
    dp.add_handler(CommandHandler('next', next_chat))
    dp.add_handler(CommandHandler('settings', settings))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
