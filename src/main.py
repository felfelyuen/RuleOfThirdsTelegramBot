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
from seller_listings import *
from shopping_cart import *
from manageorders import *
from delivery import *

#insert telegram token here
    #felix key: 8131399573:AAGYyedk735WuHa7SRcoxiKGx4lChQ7-0Vk
    #gab key: 7825728929:AAGXm4iEX14ly4fQo2GIpkv9ZRuLpRDgvPc
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
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)

    if user_role == "buyer":
        #display buyer menu
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Rule Of Thirds Messaging Bot!\n"
             "What would you like to do today?\n\n"
             "==================================\n"
             "/listings to view our listings and add to cart\n"
             "/cart to view your shopping cart and checkout\n"
             "/delivery to input delivery information (after payment is verified)"
             "/FAQ to view our FAQs\n"
             "==================================")
    else:
        #display seller menu
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Rule Of Thirds Messaging Bot! What would you like to do today?\n"+
             "/manageListings manage listings\n"
             "/manageCatalogue manage catalogue\n"
             "/manageorders manage orders")

async def handlerUnknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    handles unknown commands
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.")

async def handlerQuestionShowFAQ(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        entry_points=[CommandHandler('listings', listings_Start)],
        states={
            LISTING_CHOOSE_CAMERA: [CallbackQueryHandler(listings_Choosing)],
            LISTING_AFTERCHOSEN: [CallbackQueryHandler(listings_Start, pattern="^back$"),
                                  CallbackQueryHandler(listings_Enquiry, pattern="qn"),
                                  CallbackQueryHandler(listings_Buying_ChooseCharm)],
            LISTING_BUYING_ADDON: [CallbackQueryHandler(listings_Choosing, pattern = "back"),
                                   CallbackQueryHandler(listings_Buying_ChooseAddOns)],
            LISTING_BUYING_CONFIRMATION: [CallbackQueryHandler(listings_Buying_ChooseCharm, pattern ="back"),
                                          CallbackQueryHandler(listings_Buying_Confirmation)],
            LISTING_BUYING_ADDEDTOCART: [CallbackQueryHandler(listings_Buying_AddedToCart, pattern="^yes$"),
                                         CallbackQueryHandler(listings_Buying_ChooseAddOns)]
        },
        fallbacks=[CommandHandler('cancel', listings_Fallback)]
    )

    editListings_handler = ConversationHandler(
        entry_points=[CommandHandler('editlistings', editListings_Start)],
        states={
            EDIT_LISTING_START: [CallbackQueryHandler(editListings_Add_Start, pattern="^add$"),
                                 CallbackQueryHandler(editListings_Delete_Start, pattern="^delete$")],
            ADD_LISTING_CONFIRM: [CallbackQueryHandler(editListings_Add_Confirmation)],
            ADD_LISTING_SUCCESS: [CallbackQueryHandler(editListings_Add_Success, pattern = "Y"),
                                  CallbackQueryHandler(editListings_Add_Start, pattern="N")],
            DELETE_LISTING_CHOSEN: [CallbackQueryHandler(editListings_Delete_Confirmation)],
            DELETE_LISTING_CONFIRMATION: [CallbackQueryHandler(editListings_Delete_Start, pattern="N"),
                                          CallbackQueryHandler(editListings_Delete_Success, pattern="Y")]
        },
        fallbacks=[CommandHandler('cancel', editListings_Cancel)]
    )

    cart_handler = ConversationHandler(
        entry_points=[CommandHandler('cart', cart_Start)],
        states={
            CART_EDIT: [CallbackQueryHandler(cart_RemoveItem, pattern="^remove$"),
                        CallbackQueryHandler(cart_Clear_Confirm, pattern="^clear$"),
                        CallbackQueryHandler(cart_Pay_Confirm, pattern="^checkout$")],
            CART_REMOVE_CONFIRM: [CallbackQueryHandler(cart_Remove_Confirm)],
            CART_REMOVE_COMPLETE: [CallbackQueryHandler(cart_RemoveItem, pattern="^back$"),
                                CallbackQueryHandler(cart_Remove_Complete)],
            CART_CLEAR_COMPLETE: [CallbackQueryHandler(cart_Start, pattern="^back$"),
                                  CallbackQueryHandler(cart_Clear_Complete)],
            CART_PAY_CONFIRM: [CallbackQueryHandler(cart_Start, pattern="^back$"),
                               CallbackQueryHandler(cart_Pay_ChooseDelivery)],
            CART_PAY_WAITING_PAYMENT: [CallbackQueryHandler(cart_Pay_Generic)]
        },
        fallbacks=[CommandHandler('cancel',handlerCartCancel)]
    )

    manageorders_handler = ConversationHandler(
        entry_points=[CommandHandler('manageorders', manageOrders_Start)],
        states={
            MANAGEORDER_START: [CallbackQueryHandler(manageOrders_verifyPayment_listCustomers, pattern="^verify$"),
                                 CallbackQueryHandler(manageOrders_sendParcel_listCustomers, pattern="^send$")],
            MANAGEORDER_PAYMENT_CONFIRMATION: [CallbackQueryHandler(manageOrders_Start, pattern="^back$"),
                                                CallbackQueryHandler(manageOrders_verifyPayment_Confirmation)],
            MANAGEORDER_PAYMENT_DELIVERYINFOASKED: [CallbackQueryHandler(manageOrders_verifyPayment_listCustomers, pattern="^back$"),
                                               CallbackQueryHandler(manageOrders_askCustomerForDeliveryInfo)],
            MANAGE_ORDER_DELIVERY_CHOOSECOURIER:[CallbackQueryHandler(manageOrders_Start, pattern="^back$"),
                                                 CallbackQueryHandler(manageOrders_sendParcel_getRate_listCouriers)],
            MANAGEORDER_DELIVERY_REQUEST_CONFIRMATION: [CallbackQueryHandler(manageOrders_sendParcel_listCustomers, pattern="^back$"),
                                                        CallbackQueryHandler(manageOrders_sendParcel_getRate_confirmation)],
            MANAGEORDER_DELIVERY_MAKEORDER:[CallbackQueryHandler(manageOrders_sendParcel_getRate_listCouriers, pattern="back"),
                                            CallbackQueryHandler(manageOrders_sendParcel_makeOrder)]

        },
        fallbacks=[CommandHandler('cancel',manageOrders_cancel)]
    )

    delivery_handler = ConversationHandler(
        entry_points=[CommandHandler('delivery', delivery_start)],
        states={
            DELIVERY_START: [CallbackQueryHandler(delivery_fillInInfo)],
            DELIVERY_ASKING_INFO: [MessageHandler(filters.TEXT, delivery_confirmDeliveryInfo)],
            DELIVERY_CONFIRMATION:[CallbackQueryHandler(delivery_fillInInfo, pattern="^no$"),
                                  CallbackQueryHandler(delivery_DeliveryInfoComplete)]
        },
        fallbacks=[CommandHandler('cancel',manageOrders_cancel)]
    )
    #add commands
    application.add_handler(start_handler)
    application.add_handler(FAQ_handler)
    application.add_handler(listing_handler)
    application.add_handler(editListings_handler)
    application.add_handler(cart_handler)
    application.add_handler(manageorders_handler)
    application.add_handler(delivery_handler)

    #default commands (do not put unknown_handler above other handlers)
    application.add_handler(unknown_handler)

    #run until cancel operation (Ctrl+C)
    application.run_polling()