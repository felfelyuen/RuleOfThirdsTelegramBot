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

def setUpTestListings():
    #listings = []
    cam1 = Camera("Sony", "Cybershot DSC-WX1", "yes", "", "16.1", "This is a Sony Cybershot DSC-WX1\nIt's really good you should buy it\n \nreally really")
    cam2 = Camera("Nikon", "Coolpix L1", "", "AA", "10","This is a Nikon Coolpix L1\nPrice point ONE THOUSAND DOLLARS")
    cam3 = Camera("Canon", "Ixy 120", "", "", "16", "This is the Canon Ixy 120\nThis is also a text message")

    listings =[cam1, cam2, cam3]

    return listings

listings = setUpTestListings()

LISTING_START, LISTING_BUYING, LISTING_CHOSEN = range(3)

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
        camera_name = x.brand + " " + x.model
        keyboard.append([InlineKeyboardButton(text=camera_name, callback_data=i)])
        i += 1

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Here is the catalogue! Click on any button to view the camera and buy!",
        reply_markup=reply_markup)

    return LISTING_CHOSEN

async def handlerListingChoosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    camera_name = query.data
    if (camera_name == "buy"):
        return LISTING_CHOSEN
    if (camera_name == "cancel"):
        return LISTING_CHOSEN
    camera_message = ""
    global listings
    camera_message = listings[int(query.data)].message

    new_keyboard = [[InlineKeyboardButton("Buy!", callback_data="buy"),
                     InlineKeyboardButton("Cancel", callback_data="cancel")]]
    await query.edit_message_text(text=camera_message, reply_markup=InlineKeyboardMarkup(new_keyboard))
    return LISTING_CHOSEN
    # await query.edit_message_reply_markup(reply_markup=new_keyboard)

async def handlerListingBuying (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="buying..."
    )
    return ConversationHandler.END

async def handlerListingFallback (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="exiting..."
    )
    return ConversationHandler.END