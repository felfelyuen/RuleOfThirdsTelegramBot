import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler, CallbackQueryHandler)
from handleQuestion import *
from listings import *
from newlistings import *

#insert telegram token here
TELEGRAM_TOKEN = '8131399573:AAGYyedk735WuHa7SRcoxiKGx4lChQ7-0Vk'

#configs basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

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
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

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
    FAQ_handler = CommandHandler('FAQ', handlerQuestionShowFAQ)

    listing_handler = ConversationHandler(
        entry_points=[CommandHandler('listings', handlerListingStart)],
        states={
            #LISTING_START: [CallbackQueryHandler(handlerListingStart, pattern="^cancel$")],
            #LISTING_BUYING: [CallbackQueryHandler(handlerListingBuying, pattern ="^buy$")],
            LISTING_CHOSEN: [#CallbackQueryHandler(handlerListingStart, pattern="^cancel$"),
                             #CallbackQueryHandler(handlerListingBuying, pattern ="^buy$"),
                             CallbackQueryHandler(handlerListingChoosing)],
            LISTING_AFTERCHOSEN: [CallbackQueryHandler(handlerListingStart, pattern="^cancel$"),
                                  CallbackQueryHandler(handlerListingBuying_ChooseCharm, pattern ="^buy$")],
            LISTING_BUYING_ADDON: [CallbackQueryHandler(handlerListingBuying_ChooseAddOns)],
            LISTING_BUYING_PAYMENT: [CallbackQueryHandler(handlerListingBuying_Payment)]
        },
        fallbacks=[CommandHandler('cancel', handlerListingFallback)]
    )

    addNewListings_handler = ConversationHandler(
        entry_points=[CommandHandler('newlistings', handlerAddListingStart)],
        states={
            ADD_LISTING_CHOOSE_QTY: [CallbackQueryHandler(handlerAddListingChooseQty)],
            ADD_LISTING_SUCCESS: [CallbackQueryHandler(handlerAddListingSuccess)]
        },
        fallbacks=[CommandHandler(handlerAddListingCancel)]
    )
    #add commands
    application.add_handler(start_handler)
    application.add_handler(question_handler)
    application.add_handler(FAQ_handler)
    application.add_handler(listing_handler)
    application.add_handler(addNewListings_handler)


    #default commands (do not put unknown_handler above other handlers)
    application.add_handler(unknown_handler)

    #run until cancel operation (Ctrl+C)
    application.run_polling()