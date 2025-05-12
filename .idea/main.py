import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler)
from handleQuestion import *

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
    #replace TOKEN with telegram bot token
    application = ApplicationBuilder().token('TOKEN').build()

    #initialise the commands
    start_handler = CommandHandler('start', handlerStart)
    unknown_handler = MessageHandler(filters.COMMAND, handlerUnknown)
    question_handler = ConversationHandler(
        entry_points=[CommandHandler('questions', handlerQuestionStart)],
        states={
            QUESTION_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlerQuestionAskSeller),
                             CommandHandler('FAQ', handlerQuestionShowFAQ)]

        },
        fallbacks=[CommandHandler('cancel', handlerQuestionFallback)]
    )
    #add commands
    application.add_handler(start_handler)
    application.add_handler(question_handler)

    #default commands (do not put unknown_handler above other handlers)
    application.add_handler(unknown_handler)

    #run until cancel operation (Ctrl+C)
    application.run_polling()