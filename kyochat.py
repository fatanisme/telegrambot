from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from pymongo import MongoClient
from bottokens import KYOCHAT_BOT_TOKEN
import time

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['telegram_bot']
users_collection = db['users']
chats_collection = db['chats']

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = users_col.find_one({'user_id': user_id})
    
    if not user:
        users_col.insert_one({
            'user_id': user_id,
            'gender': None,
            'age': None,
            'city': None,
            'likes': 0,
            'dislikes': 0,
            'report_count': 0,
            'report_list': [],
        })
    
    keyboard = [
        ['Find a Partner', 'Find by Gender']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Welcome to Anonymous Chat Bot! You can start searching for a partner now.", reply_markup=reply_markup)

def gender_selection(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Male", callback_data='male')],
        [InlineKeyboardButton("Female", callback_data='female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please select your gender:', reply_markup=reply_markup)

def gender_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    gender = query.data
    
    users_col.update_one({'user_id': user_id}, {'$set': {'gender': gender}})
    
    query.answer()
    query.edit_message_text(text=f"Gender set to {gender.capitalize()}.")
    
    # Proceed to join chat pool
    join(update, context)

def join(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = users_col.find_one({'user_id': user_id})
    
    # Add to chat pool
    chats_col.update_one({'user_id': user_id}, {'$set': {'status': 'waiting'}}, upsert=True)
    
    # Attempt to match with another user
    match_users(user_id, user['gender'])

def match_users(user_id, gender):
    # Matching logic based on gender preference
    partner = chats_col.find_one({
        'user_id': {'$ne': user_id},
        'status': 'waiting',
        'gender': {'$ne': gender}
    })
    
    if partner:
        # Start chat session
        start_chat(user_id, partner['user_id'])
    else:
        # No match found yet
        pass

def start_chat(user_id1, user_id2):
    chat_id = chats_col.insert_one({
        'users': [user_id1, user_id2],
        'start_time': time.time(),
        'messages': []
    }).inserted_id
    
    chats_col.update_many({'user_id': {'$in': [user_id1, user_id2]}}, {'$set': {'status': 'in_chat', 'chat_id': chat_id}})
    
    context.bot.send_message(chat_id=user_id1, text="You have been connected to a chat partner!")
    context.bot.send_message(chat_id=user_id2, text="You have been connected to a chat partner!")

def leave(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat = chats_col.find_one({'users': user_id, 'status': 'in_chat'})
    
    if chat:
        partner_id = next(user for user in chat['users'] if user != user_id)
        feedback_keyboard = [
            [InlineKeyboardButton("👍", callback_data='like'), InlineKeyboardButton("👎", callback_data='dislike')],
            [InlineKeyboardButton("Report", callback_data='report')]
        ]
        reply_markup = InlineKeyboardMarkup(feedback_keyboard)
        update.message.reply_text("You have left the chat. How was your experience?", reply_markup=reply_markup)
        
        # Notify partner
        context.bot.send_message(chat_id=partner_id, text="Your chat partner has left the conversation. Use /join to find a new partner.")
        
        # End chat session
        chats_col.delete_one({'_id': chat['_id']})
        users_col.update_many({'user_id': {'$in': [user_id, partner_id]}}, {'$set': {'status': 'available'}})

def feedback_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if data == 'like':
        # Increase likes for the partner
        pass
    elif data == 'dislike':
        # Increase dislikes for the partner
        pass
    elif data == 'report':
        report_user(update, context)
        
    query.answer()
    query.edit_message_text(text="Thank you for your feedback.")

def report_user(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Advertising", callback_data='advertising')],
        [InlineKeyboardButton("Selling", callback_data='selling')],
        [InlineKeyboardButton("Child Porn", callback_data='child_porn')],
        [InlineKeyboardButton("Begging", callback_data='begging')],
        [InlineKeyboardButton("Insulting", callback_data='insulting')],
        [InlineKeyboardButton("Violence", callback_data='violence')],
        [InlineKeyboardButton("Vulgar Partner", callback_data='vulgar')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('Select a report reason:', reply_markup=reply_markup)
    
def report_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    report_reason = query.data
    user_id = query.from_user.id
    partner_id = None  # Retrieve partner ID
    
    if report_reason != 'cancel':
        users_col.update_one({'user_id': partner_id}, {
            '$inc': {'report_count': 1},
            '$push': {'report_list': report_reason}
        })
    
    query.answer()
    query.edit_message_text(text="Report submitted. Thank you.")

def main():
    updater = Updater(KYOCHAT_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("join", join))
    dp.add_handler(CommandHandler("leave", leave))
    dp.add_handler(CommandHandler("next", leave))
    
    dp.add_handler(CallbackQueryHandler(gender_callback, pattern='^(male|female)$'))
    dp.add_handler(CallbackQueryHandler(feedback_callback, pattern='^(like|dislike|report)$'))
    dp.add_handler(CallbackQueryHandler(report_callback, pattern='^(advertising|selling|child_porn|begging|insulting|violence|vulgar|cancel)$'))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
