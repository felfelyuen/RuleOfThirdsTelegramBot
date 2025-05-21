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

'''
=========================================================================
BUYER LISTING FUNCTIONS
Where there are functions to let the buyer edit the listings by either
1.Adding
2.Deleting
3.Changing the quantity
=========================================================================
'''

#Using a test catalogue for now
global catalogue
catalogue = setUpTestListings()

EDIT_LISTING_START, ADD_LISTING_CHOOSE_QTY, ADD_LISTING_SUCCESS, QUANTITY_CHANGE_CHOSEN, QUANTITY_CHANGE_SUCCESS= range(5)

async def handlerEditListingStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Add listing", callback_data="add")],
        [InlineKeyboardButton("Change quantity", callback_data="changeqty")],
        [InlineKeyboardButton("Delete listing", callback_data="delete")]
    ]
    await update.message.reply_text(text="What do you want to change in the listings today?",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_LISTING_START

'''
=========================================================================
ADD LISTING FUNCTIONS
=========================================================================
'''

async def handlerAddListingStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles convo where seller has to choose which camera from the catalogue to add into the listing list.
    """
    query = update.callback_query
    await query.answer()
    #retrieve whole catalogue
    global catalogue

    #set up buttons in message
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

    await query.edit_message_text(
        text="Let's add a new listing! Take the listing from the catalogue",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADD_LISTING_CHOOSE_QTY

async def handlerAddListingChooseQty (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles asking how many cameras to add into the listing
    """
    query = update.callback_query
    await query.answer()

    global catalogue
    indexCamera = catalogue[int(query.data)]
    #TODO: CHANGE FORMAT INTO TYPE THE ANSWER INSTEAD OF THIS BUTTONS
    keyboard = [[InlineKeyboardButton(text="1", callback_data=query.data + " 1")],
                [InlineKeyboardButton(text="2", callback_data=query.data + " 2")],
                [InlineKeyboardButton(text="3", callback_data= query.data + " 3")]]

    await query.edit_message_text(text="You have chosen: " + indexCamera.name + "\nNow, choose how many cameras to add into the listing",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_LISTING_SUCCESS

async def handlerAddListingSuccess (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the actual addition of the listing into the listing.
    """
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

    return ConversationHandler.END

'''
=========================================================================
CHANGE QUANTITY OF LISTINGS FUNCTIONS
=========================================================================
'''

async def handlerChangeQTYStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the start of convo with change in quantity for a listing item
    """
    query = update.callback_query
    await query.answer()

    #get listings
    editedListings = listings.listings
    keyboard = []
    #make keyboard
    i = 0
    while i < len(editedListings):
        x = editedListings[i]
        camera_name = x.name
        keyboard.append([InlineKeyboardButton(text=camera_name, callback_data=i)])
        i += 1

    await query.edit_message_text(text="Which camera do you want to change the quantity of?",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return QUANTITY_CHANGE_CHOSEN

async def handlerChangeQTYChooseQTY (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the convo where a quantity is required to be inputted
    """
    query = update.callback_query
    await query.answer()

    global camera_choice
    camera_choice = int(query.data)
    indexCameraName = listings.listings[camera_choice].name

    await query.edit_message_text(text="Okay cool! You chosen: " + indexCameraName +
                                    "\nWhat new quantity do you want this camera to have?")
    return QUANTITY_CHANGE_SUCCESS

async def handlerChangeQTYSuccess (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the actual change in quantity for that camera in that listing.
    """
    #TODO NEED TO HANDLE IF AMOUNT INPUTTED IS NOT INTEGER
    newAmount = int(update.message.text)
    #get listings
    editedListings = listings.listings

    #get camera choice
    global camera_choice
    indexCamera = editedListings[camera_choice]
    indexCamera.quantity = newAmount
    #TODO PROBABLY WILL CHANGE THIS CODE AFTER I ADDED DELETION BUT ANYWAY
    #assume newAmount is non-zero
    #i will amend this soon

    #set listings to editedListings
    listings.listings = editedListings
    
    await update.message.reply_text(text="Okay! The camera " + indexCamera.name + " has a new quantity of " + str(newAmount))

    return ConversationHandler.END


async def handlerEditListingCancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Fallback if the user decides to cancel halfway.
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(chat_id=update.effective_chat.id,text="Edit listing action cancelled")
    return ConversationHandler.END

