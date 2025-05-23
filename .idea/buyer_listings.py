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

(EDIT_LISTING_START,
 ADD_LISTING_CHOOSE_QTY,
 ADD_LISTING_SUCCESS,
 DELETE_LISTING_CHOSEN,
 DELETE_LISTING_CONFIRMATION,
 QUANTITY_CHANGE_CHOSEN,
 QUANTITY_CHANGE_SUCCESS) = range(7)

async def handlerEditListingStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the start of conversation of editing the listings
    """
    keyboard = [
        [InlineKeyboardButton("Add listing", callback_data="add")],
        [InlineKeyboardButton("Change quantity", callback_data="changeqty")],
        [InlineKeyboardButton("Delete listing", callback_data="delete")]
    ]
    await update.message.reply_text(text="What do you want to change in the listings today?"
                                         "Use /cancel to exit the edit listings mode at any time",
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

    #set up keyboard buttons
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

    global camera_choice
    camera_choice = query.data

    global catalogue
    indexCamera = catalogue[int(camera_choice)]
    message = "You have chosen: " + indexCamera.name + "\n"

    #check if camera is inside the listings already
    editedListing = listings.listings
    i = 0
    while i < len(editedListing):
        if (editedListing[i].name == indexCamera.name):
            break
        i += 1
    if i < len(editedListing) :
        #inside listing
        currentStock = editedListing[i].quantity
        message += ("The camera is ALREADY INSIDE your listings.\n"
                   "How many cameras do you want to add into the listing?\n\n"
                   "Current stock: " + str(currentStock))
        camera_choice += " OLD " + str(i)
    else:
        #completely new listing
        message += ("This is a COMPLETELY NEW listing!\n"
                    "How many cameras do you want to add into the listing?")
        camera_choice += " NEW"

    await query.edit_message_text(text=message)
    return ADD_LISTING_SUCCESS

async def handlerAddListingSuccess (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the actual addition of the listing into the listing.
    """
    amount = update.message.text
    if amount.isdigit() == False:
        await update.message.reply_text(text="Invalid input registered. Please try again. How many cameras do you want to add into the stock?")
        return ADD_LISTING_SUCCESS
    newAmount = int(amount)
    global camera_choice
    choices = camera_choice.split(" ")

    global catalogue
    indexCamera = catalogue[int(choices[0])]
    message = ""

    #fetch listings list
    editedListing = listings.listings

    if (choices[1] == "OLD"):
        #add to the quantity
        index = int(choices[2])
        editedListing[index].quantity += newAmount
        message = ("The camera " + indexCamera.name +
                   " has added in quantity of " + amount + "\n" +
                   "Total quantity of camera is now: " + str(editedListing[index].quantity))
    else:
        #append to the listing list
        indexCamera.quantity = newAmount
        editedListing.append(indexCamera)
        message = ("The camera " + indexCamera.name +
                   " is newly added into the listings." + "\n" +
                   "Total quantity of camera is now: " + amount)

    #make listings the editedListing
    listings.listings = editedListing
    await update.message.reply_text(text="Listing updated!\n" + message)

    return ConversationHandler.END

'''
=========================================================================
DELETE LISTINGS FUNCTIONS
=========================================================================
'''

async def handlerDeleteListingStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the start of deleting listing: asking which camera to delete off the listing
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

    await query.edit_message_text(text="Which camera do you want to delete the listing of?",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return DELETE_LISTING_CHOSEN

async def handlerDeleteConfirmation (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles confirmation of listing deletion.
    If pressed no, it will go back to before.
    """
    query = update.callback_query
    await query.answer()

    index = query.data
    editedListings = listings.listings
    indexCamera = editedListings[int(index)]
    keyboard = [[InlineKeyboardButton(text="yes", callback_data="Y " + index),
                 InlineKeyboardButton(text="go back", callback_data="N " + index)]]
    await query.edit_message_text(text="Are you sure you want to delete this camera listing?\n" +
                                       indexCamera.name + "\n" +
                                       "Quantity of: " + str(indexCamera.quantity),
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return DELETE_LISTING_CONFIRMATION

async def handlerDeleteSuccess (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles actual deletion of the listing.
    """
    query = update.callback_query
    await query.answer()
    index = int(query.data[2:])
    indexCamera = listings.listings[index]
    #remove the camera
    listings.listings.pop(index)

    await query.edit_message_text(text="Listing: \"" + indexCamera.name + "\" has been removed from the listing.")
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
    amount = update.message.text
    if amount.isdigit() == False:
        await update.message.reply_text(text="Invalid input registered. Please try again. What quantity do you want the camera to have?")
        return QUANTITY_CHANGE_SUCCESS

    newAmount = int(update.message.text)
    #get listings
    editedListings = listings.listings

    #get camera choice
    global camera_choice
    indexCamera = editedListings[camera_choice]

    message = "Okay! The camera " + indexCamera.name + " has a new quantity of " + str(newAmount)
    if newAmount == 0:
        #delete listing due to zero quantity left
        editedListings.pop(camera_choice)
        message += "\n The listing has been removed due to there being 0 quantity left."
    else:
        editedListings[camera_choice].quantity = newAmount

    #set listings to editedListings
    listings.listings = editedListings
    
    await update.message.reply_text(text=message)

    return ConversationHandler.END


async def handlerEditListingCancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Fallback if the user decides to cancel halfway.
    """
    await update.message.reply_text(text="Edit listing action cancelled")
    return ConversationHandler.END

