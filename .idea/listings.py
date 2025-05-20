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


LISTING_START, LISTING_CHOSEN, LISTING_AFTERCHOSEN, LISTING_BUYING_ADDON, LISTING_BUYING_PAYMENT = range(5)

async def handlerListingStart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    handles start of conversation with catalogue
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
        text="Here is the catalogue! Click on any button to view the camera and buy!\n Use /cancel to exit the catalogue",
        reply_markup=reply_markup)

    return LISTING_CHOSEN

async def handlerListingChoosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()

    global listings
    camera_message = listings[int(query.data)].message

    new_keyboard = [[InlineKeyboardButton("Buy!", callback_data="buy"),
                     InlineKeyboardButton("Cancel", callback_data="cancel")]]
    await query.edit_message_text(text=camera_message, reply_markup=InlineKeyboardMarkup(new_keyboard))
    return LISTING_AFTERCHOSEN
    # await query.edit_message_reply_markup(reply_markup=new_keyboard)

async def handlerListingBuying_ChooseCharm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    query = update.callback_query
    await query.answer()

    #delivery details to be worked out in v1.1

    await query.edit_message_text(
        text="END OF CONVO (V1.0) (" + query.data + ")"
    )
    return ConversationHandler.END

async def handlerListingFallback (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exited Catalogue mode"
    )
    return ConversationHandler.END