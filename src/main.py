import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler, CallbackQueryHandler)
from login import get_user_role
from handleQuestion import *
from listings import *
from buyer_listings import *

#insert telegram token here
    #felix key: 8131399573:AAGYyedk735WuHa7SRcoxiKGx4lChQ7-0Vk
    #gab key: 7825728929:AAGXm4iEX14ly4fQo2GIpkv9ZRuLpRDgvPc
TELEGRAM_TOKEN = '7825728929:AAGXm4iEX14ly4fQo2GIpkv9ZRuLpRDgvPc'

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
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)

    if user_role == "buyer":
        #display buyer menu
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Rule Of Thirds Messaging Bot! What would you like to do today?\n"+
             "/questions ask questions\n"
             "/listings view our listings\n")
    else:
        #display seller menu
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Rule Of Thirds Messaging Bot! What would you like to do today?\n"+
             "/manageListings manage listings\n"
             "/manageCatalogue manage catalogue")

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
            LISTING_CHOOSE_CAMERA: [CallbackQueryHandler(handlerListingChoosing)],
            LISTING_AFTERCHOSEN: [CallbackQueryHandler(handlerListingStart, pattern="^back$"),
                                  CallbackQueryHandler(handlerListingBuying_ChooseCharm, pattern ="^buy$")],
            LISTING_BUYING_ADDON: [CallbackQueryHandler(handlerListingBuying_ChooseAddOns)],
            LISTING_BUYING_PAYMENT: [CallbackQueryHandler(handlerListingBuying_Payment)]
        },
        fallbacks=[CommandHandler('cancel', handlerListingFallback)]
    )

    editListings_handler = ConversationHandler(
        entry_points=[CommandHandler('editlistings', handlerEditListingStart)],
        states={
            EDIT_LISTING_START: [CallbackQueryHandler(handlerAddListingStart, pattern="^add$"),
                                 CallbackQueryHandler(handlerChangeQTYStart, pattern="^changeqty$"),
                                 CallbackQueryHandler(handlerDeleteListingStart, pattern="^delete$")],
            ADD_LISTING_CHOOSE_QTY: [CallbackQueryHandler(handlerAddListingChooseQty)],
            ADD_LISTING_SUCCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlerAddListingSuccess)],
            DELETE_LISTING_CHOSEN: [CallbackQueryHandler(handlerDeleteConfirmation)],
            DELETE_LISTING_CONFIRMATION: [CallbackQueryHandler(handlerDeleteListingStart, pattern="N"),
                                          CallbackQueryHandler(handlerDeleteSuccess, pattern="Y")],
            QUANTITY_CHANGE_CHOSEN: [CallbackQueryHandler(handlerChangeQTYChooseQTY)],
            QUANTITY_CHANGE_SUCCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlerChangeQTYSuccess)]
        },
        fallbacks=[CommandHandler('cancel', handlerEditListingCancel)]
    )
    #add commands
    application.add_handler(start_handler)
    application.add_handler(question_handler)
    application.add_handler(FAQ_handler)
    application.add_handler(listing_handler)
    application.add_handler(editListings_handler)


    #default commands (do not put unknown_handler above other handlers)
    application.add_handler(unknown_handler)

    #run until cancel operation (Ctrl+C)
    application.run_polling()