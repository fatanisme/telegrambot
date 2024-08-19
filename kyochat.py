from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes, CallbackContext
from pymongo import MongoClient
from bottokens import KYOCHAT_BOT_TOKEN
import time

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['telegram_bot']
users_col = db['users']
chats_col = db['chats']

async def start(update: Update, context: CallbackContext):
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
    await update.message.reply_text("Welcome to Anonymous Chat Bot! You can start searching for a partner now.", reply_markup=reply_markup)

async def gender_selection(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Male", callback_data='male')],
        [InlineKeyboardButton("Female", callback_data='female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select your gender:', reply_markup=reply_markup)

async def gender_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    gender = query.data
    
    users_col.update_one({'user_id': user_id}, {'$set': {'gender': gender}})
    
    query.answer()
    query.edit_message_text(text=f"Gender set to {gender.capitalize()}.")
    
    # Proceed to join chat pool
    join(update, context)

async def join(update: Update, context):
    user_id = update.message.from_user.id
    user = users_col.find_one({"user_id": user_id})

    if user is None:
        # If the user doesn't exist in the database, insert a new record
        users_col.insert_one({"user_id": user_id})
        user = users_col.find_one({"user_id": user_id})
    
    # Check if 'gender' exists in the user's record
    if 'gender' not in user:
        await update.message.reply_text("Your gender is not set. Please use /settings to set your gender before joining the chat pool.")
        return
    
    # Proceed with joining the chat pool if the gender is set
    await match_users(user_id, user['gender'])


async def match_users(user_id, gender):
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

async def start_chat(user_id1, user_id2):
    chat_id = chats_col.insert_one({
        'users': [user_id1, user_id2],
        'start_time': time.time(),
        'messages': []
    }).inserted_id
    
    chats_col.update_many({'user_id': {'$in': [user_id1, user_id2]}}, {'$set': {'status': 'in_chat', 'chat_id': chat_id}})
    
    context.bot.send_message(chat_id=user_id1, text="You have been connected to a chat partner!")
    context.bot.send_message(chat_id=user_id2, text="You have been connected to a chat partner!")

async def leave(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat = chats_col.find_one({'users': user_id, 'status': 'in_chat'})
    
    if chat:
        partner_id = next(user for user in chat['users'] if user != user_id)
        feedback_keyboard = [
            [InlineKeyboardButton("👍", callback_data='like'), InlineKeyboardButton("👎", callback_data='dislike')],
            [InlineKeyboardButton("Report", callback_data='report')]
        ]
        reply_markup = InlineKeyboardMarkup(feedback_keyboard)
        await update.message.reply_text("You have left the chat. How was your experience?", reply_markup=reply_markup)
        
        # Notify partner
        context.bot.send_message(chat_id=partner_id, text="Your chat partner has left the conversation. Use /join to find a new partner.")
        
        # End chat session
        chats_col.delete_one({'_id': chat['_id']})
        users_col.update_many({'user_id': {'$in': [user_id, partner_id]}}, {'$set': {'status': 'available'}})

async def feedback_callback(update: Update, context: CallbackContext):
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

async def report_user(update: Update, context: CallbackContext):
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
    
async def report_callback(update: Update, context: CallbackContext):
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
    application = ApplicationBuilder().token(KYOCHAT_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CommandHandler("next", leave))
    
    application.add_handler(CallbackQueryHandler(gender_callback, pattern='^(male|female)$'))
    application.add_handler(CallbackQueryHandler(feedback_callback, pattern='^(like|dislike|report)$'))
    application.add_handler(CallbackQueryHandler(report_callback, pattern='^(advertising|selling|child_porn|begging|insulting|violence|vulgar|cancel)$'))
    
    application.run_polling()

if __name__ == '__main__':
    main()
