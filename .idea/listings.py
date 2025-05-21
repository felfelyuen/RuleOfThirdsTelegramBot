import requests
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler)
from camera import Camera
from purchase_info import PurchaseInfo

def setUpTestListings():
    #listings = []
    cam1 = Camera("Sony", "Cybershot DSC-WX1", "yes", "", "16.1", 1,"This is a Sony Cybershot DSC-WX1\nIt's really good you should buy it\n \nreally really")
    cam2 = Camera("Nikon", "Coolpix L1", "", "AA", "10",1,"This is a Nikon Coolpix L1\nPrice point ONE THOUSAND DOLLARS")
    cam3 = Camera("Canon", "Ixy 120", "", "", "16", 2,"This is the Canon Ixy 120\nThis is also a text message")

    listings =[cam1, cam2, cam3]

    return listings

listings = setUpTestListings()


LISTING_START, LISTING_CHOOSE_CAMERA, LISTING_AFTERCHOSEN, LISTING_BUYING_ADDON, LISTING_BUYING_PAYMENT = range(5)

async def handlerListingStart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    handles start of conversation with listings
    """

    #retrieve listings
    global listings

    keyboard = []
    i = 0
    while i < len(listings):
        x = listings[i]
        camera_name = x.name
        keyboard.append([InlineKeyboardButton(text=camera_name, callback_data=i)])
        i += 1

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Here are the listings! Click on any button to view the camera and buy!\n Use /cancel to exit the listings",
        reply_markup=reply_markup)

    return LISTING_CHOOSE_CAMERA

async def handlerListingChoosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the conversation when the user is choosing which camera to buy.
    """
    query = update.callback_query
    await query.answer()

    global listings
    indexCamera = listings[int(query.data)]
    camera_message = indexCamera.message + "\nThere are currently " + str(indexCamera.quantity) + " in stock!"

    new_keyboard = [[InlineKeyboardButton("Buy!", callback_data="buy"),
                     InlineKeyboardButton("Go Back", callback_data="back")]]
    await query.edit_message_text(text=camera_message, reply_markup=InlineKeyboardMarkup(new_keyboard))
    return LISTING_AFTERCHOSEN

async def handlerListingBuying_ChooseCharm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose which camera to buy,
    now is to choose which charm to get
    """
    query = update.callback_query
    await query.answer()

    charm_keyboard = [[InlineKeyboardButton("Plain", callback_data="plain"),
                       InlineKeyboardButton("Beaded", callback_data="beaded")]]
    await query.edit_message_text(
        text="Thank you for your interest!\n" 
             "Please fill in the following!\n" 
             "Wrist strap variation?\n "
             "Use /cancel at any time to stop the procedure"
        , reply_markup=InlineKeyboardMarkup(charm_keyboard)
    )
    return LISTING_BUYING_ADDON

async def handlerListingBuying_ChooseAddOns (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose the camera and the charm,
    now is to choose any add-ons that the user may want
    """
    query = update.callback_query
    await query.answer()

    addon_keyboard = [[InlineKeyboardButton("Yes (lightning cable)", callback_data=query.data + " lightning"),
                       InlineKeyboardButton("Yes(type C cable)", callback_data=query.data + " type C"),
                       InlineKeyboardButton("No", callback_data=query.data + " no")]]
    await query.edit_message_text(
        text="Next, would you like a SD card reader? (additional $5)\n"
            "Use /cancel at any time to stop the procedure"
        , reply_markup=InlineKeyboardMarkup(addon_keyboard)
    )
    return LISTING_BUYING_PAYMENT

async def handlerListingBuying_Payment (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose the camera and the charm and the add-ons,
    now is to handle payment
    """
    query = update.callback_query
    await query.answer()

    #delivery details to be worked out in v1.1

    await query.edit_message_text(
        text="END OF CONVO (V1.0) (" + query.data + ")"
    )
    return ConversationHandler.END

async def handlerListingFallback (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation if the user cancels and it will exit the conversation and the listings mode
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exited Catalogue mode"
    )
    return ConversationHandler.END