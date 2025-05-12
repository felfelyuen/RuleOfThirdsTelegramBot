import requests
import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler)

#configs basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handlerStart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    handles /start command
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Rule Of Thirds Messaging Bot! What would you like to do today?\n"+
             "/questions ask questions\n"
             "/catalogue view our catalogue\n"
             "/buy buy a specific camera with a code")

async def handlerUnknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    handles unknown commands
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.")

if __name__ == '__main__':
    application = ApplicationBuilder().token('8131399573:AAGYyedk735WuHa7SRcoxiKGx4lChQ7-0Vk').build()

    #initialise the commands
    start_handler = CommandHandler('start', handlerStart)
    unknown_handler = MessageHandler(filters.COMMAND, handlerUnknown)
    #question_handler = CommandHandler('questions', handlerQuestions)

    #add commands
    application.add_handler(start_handler)

    #default commands (do not put unknown_handler above other handlers)
    application.add_handler(unknown_handler)

    #run until cancel operation (Ctrl+C)
    application.run_polling()