import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler, CallbackQueryHandler)
from listings import *
from buyer_listings import *
from shopping_cart import *

#insert telegram token here
TELEGRAM_TOKEN = '7028968855:AAGdZvw_--h3Juy_y9w8dWqRD4B7SpU-_9E'

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
        text="Welcome to Rule Of Thirds Messaging Bot!\n"
             "What would you like to do today?\n\n"
             "==================================\n"
             "/listings to view our listings and add to cart\n"
             "/cart to view your shopping cart and checkout\n"
             "/FAQ to view our FAQs\n"
             "==================================")

async def handlerUnknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    handles unknown commands
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.")

async def handlerQuestionShowFAQ(update:Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    shows FAQs
    """
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text="Please visit the link below for our FAQ!\n" +
             "https://docs.google.com/document/d/1v4ofc_tfiPyNuJWW-iOHLFUolAb5srZfnWqnke90Qlk/edit?tab=t.vhga5eeqazd4"
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    #initialise the commands
    start_handler = CommandHandler('start', handlerStart)
    unknown_handler = MessageHandler(filters.COMMAND, handlerUnknown)
    FAQ_handler = CommandHandler('FAQ', handlerQuestionShowFAQ)

    listing_handler = ConversationHandler(
        entry_points=[CommandHandler('listings', handlerListingStart)],
        states={
            LISTING_CHOOSE_CAMERA: [CallbackQueryHandler(handlerListingChoosing)],
            LISTING_AFTERCHOSEN: [CallbackQueryHandler(handlerListingStart, pattern="^back$"),
                                  CallbackQueryHandler(handlerListing_Enquiry, pattern="qn"),
                                  CallbackQueryHandler(handlerListingBuying_ChooseCharm)],
            LISTING_BUYING_ADDON: [CallbackQueryHandler(handlerListingChoosing, pattern = "back"),
                                   CallbackQueryHandler(handlerListingBuying_ChooseAddOns)],
            LISTING_BUYING_CONFIRMATION: [CallbackQueryHandler(handlerListingBuying_ChooseCharm, pattern ="back"),
                                          CallbackQueryHandler(handlerListingBuying_Confirmation)],
            LISTING_BUYING_ADDEDTOCART: [CallbackQueryHandler(handlerListingBuying_AddedToCart, pattern="^yes$"),
                                         CallbackQueryHandler(handlerListingBuying_ChooseAddOns)]
        },
        fallbacks=[CommandHandler('cancel', handlerListingFallback)]
    )

    editListings_handler = ConversationHandler(
        entry_points=[CommandHandler('editlistings', handlerEditListingStart)],
        states={
            EDIT_LISTING_START: [CallbackQueryHandler(handlerAddListingStart, pattern="^add$"),
                                 CallbackQueryHandler(handlerDeleteListingStart, pattern="^delete$")],
            ADD_LISTING_CONFIRM: [CallbackQueryHandler(handlerAddListingConfirmation)],
            ADD_LISTING_SUCCESS: [CallbackQueryHandler(handlerAddListingSuccess, pattern = "Y"),
                                  CallbackQueryHandler(handlerAddListingStart, pattern="N")],
            DELETE_LISTING_CHOSEN: [CallbackQueryHandler(handlerDeleteConfirmation)],
            DELETE_LISTING_CONFIRMATION: [CallbackQueryHandler(handlerDeleteListingStart, pattern="N"),
                                          CallbackQueryHandler(handlerDeleteSuccess, pattern="Y")]
        },
        fallbacks=[CommandHandler('cancel', handlerEditListingCancel)]
    )

    cart_handler = ConversationHandler(
        entry_points=[CommandHandler('cart', handlerCartStart)],
        states={
            CART_EDIT: [CallbackQueryHandler(handlerCartRemoveItem, pattern="^remove$"),
                        CallbackQueryHandler(handlerCartClearConfirm, pattern="^clear$"),
                        CallbackQueryHandler(handlerCartPayConfirmationPage, pattern="^checkout$")],
            CART_REMOVE_CONFIRM: [CallbackQueryHandler(handlerCartRemoveConfirm)],
            CART_REMOVE_COMPLETE: [CallbackQueryHandler(handlerCartRemoveItem, pattern="^back$"),
                                CallbackQueryHandler(handlerCartRemoveComplete)],
            CART_CLEAR_COMPLETE: [CallbackQueryHandler(handlerCartStart, pattern="^back$"),
                                  CallbackQueryHandler(handlerCartClearComplete)],
            CART_PAY_CONFIRM: [CallbackQueryHandler(handlerCartStart, pattern="^back$"),
                               CallbackQueryHandler(handlerCartPay_ChooseDelivery)],
            CART_PAY_WAITING_PAYMENT: [CallbackQueryHandler(handlerCartPay_Pickup, pattern="^pick-up$"),
                                       CallbackQueryHandler(handlerCartPay_Delivery, pattern="^delivery$"),
                                       CallbackQueryHandler(handlerCartPay_Asap, pattern="^ASAP$")]
        },
        fallbacks=[CommandHandler('cancel',handlerCartCancel)]
    )
    #add commands
    application.add_handler(start_handler)
    application.add_handler(FAQ_handler)
    application.add_handler(listing_handler)
    application.add_handler(editListings_handler)
    application.add_handler(cart_handler)


    #default commands (do not put unknown_handler above other handlers)
    application.add_handler(unknown_handler)

    #run until cancel operation (Ctrl+C)
    application.run_polling()