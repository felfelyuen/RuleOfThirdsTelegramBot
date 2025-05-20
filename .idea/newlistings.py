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

import listings
from listings import setUpTestListings

#Using a test catalogue for now
global catalogue
catalogue = setUpTestListings()

ADD_LISTING_CHOOSE_QTY, ADD_LISTING_SUCCESS = range(2)
async def handlerAddListingStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #retrieve whole catalogue
    global catalogue

    keyboard = []
    i = 0
    while i < len(catalogue):
        j = 0
        row = []
        if i + 2 < len(catalogue):
            j = i
            #amount of cameras per row is 2, so that the seller can still see the camera name
            while j < 2:
                x = catalogue[j]
                camera_name = x.name
                row.append(InlineKeyboardButton(text=camera_name, callback_data=j))
                j += 1
            i += 2
        else:
            while i < len(catalogue):
                x = catalogue[i]
                camera_name = x.name
                row.append(InlineKeyboardButton(text=camera_name, callback_data=i))
                i += 1
        keyboard.append(row)

    await context.bot.send_message(
        chat_id= update.effective_chat.id,
        text="Let's add a new listing! Take the listing from the catalogue",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADD_LISTING_CHOOSE_QTY

async def handlerAddListingChooseQty (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    global catalogue
    indexCamera = catalogue[int(query.data)]
    camera_name = indexCamera.brand + " " + indexCamera.model

    keyboard = [[InlineKeyboardButton(text="1", callback_data=query.data + " 1")],
                [InlineKeyboardButton(text="2", callback_data=query.data + " 2")],
                [InlineKeyboardButton(text="3", callback_data= query.data + " 3")]]

    await query.edit_message_text(text="You have chosen: " + camera_name + "\nNow, choose how many cameras to add into the listing",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_LISTING_SUCCESS

async def handlerAddListingSuccess (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()


    global catalogue
    indexCamera = catalogue[int(query.data[0])]
    message = ""

    #fetch listings list
    editedListing = listings.listings

    i = 0
    while (i < len(editedListing)) & (editedListing[i].name != indexCamera.name):
        i += 1
    if (i < len(editedListing)):
        #add to the quantity
        addedQuantity = int(query.data[2])
        editedListing[i].quantity += addedQuantity
        message = ("The camera " + indexCamera.name +
                   " has added in quantity of " + str(addedQuantity) + "\n" +
                   "Total quantity of camera is now: " + str(editedListing[i].quantity))
    else:
        #append to the listing list
        indexCamera.quantity = int(query.data[2])
        editedListing.append(indexCamera)
        message = ("The camera " + indexCamera.name +
                   " is newly added into the listings." + "\n" +
                   "Total quantity of camera is now: " + str(editedListing[i].quantity))

    #make listings the editedListings
    listings.listings = editedListing
    await query.edit_message_text(text="Listing updated!\n" + message)

    #await query.edit_message_text(text=str(len(editedListing)))
    return ConversationHandler.END


async def handlerAddListingCancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #query = update.callback_query
    #await query.answer()

    #await query.edit_message_text(text="Add listing action cancelled")
    await context.bot.send_message(chat_id=update.effective_chat.id,text="Add listing action cancelled")
    return ConversationHandler.END

