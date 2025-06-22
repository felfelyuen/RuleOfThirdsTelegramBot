import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from camera import Camera
from purchase_info import PurchaseInfo
from HashMap import HashMap
import shopping_cart
from cart import Cart

def setUpTestListings():
    #listings = []
    cam1 = Camera("Sony", "Cybershot DSC-WX1", "yes", "", "16.1", 169, "@taylorswif")
    cam2 = Camera("Nikon", "Coolpix L1", "", "AA", "10",189,"@ethelcain")
    cam3 = Camera("Canon", "Ixy 120", "", "", "16", 299,"@wannnts")

    listings = [cam1, cam2, cam3]

    return listings

listings = setUpTestListings()

customerPurchaseInfos = HashMap()

LISTING_START, LISTING_CHOOSE_CAMERA, LISTING_AFTERCHOSEN, LISTING_BUYING_ADDON, LISTING_BUYING_CONFIRMATION, LISTING_BUYING_ADDEDTOCART = range(6)

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
    index = query.data
    if ("back" in index):
        index = query.data[5: ]
    indexCamera = listings[int(index)]
    camera_message = indexCamera.message

    new_keyboard = [[InlineKeyboardButton("Buy!", callback_data=query.data),
                     InlineKeyboardButton("Go Back", callback_data="back"),
                     InlineKeyboardButton("Enquire about listing", callback_data="qn " + query.data)]]
    await query.edit_message_text(text=camera_message, reply_markup=InlineKeyboardMarkup(new_keyboard))
    return LISTING_AFTERCHOSEN

async def handlerListing_Enquiry (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    To handle the user's questions
    """
    query = update.callback_query
    await query.answer()

    global listings
    indexCamera = listings[int(query.data[3:])]
    seller = indexCamera.seller
    await query.edit_message_text(text=("Please message the seller: " + seller + " to ask your questions about this camera.\n" +
                                        "(We might not be able to message you due to your privacy settings)\n\n" +
                                        "Alternatively, for general concerns, please visit the link below for our FAQ!\n" +
                                        "https://docs.google.com/document/d/1v4ofc_tfiPyNuJWW-iOHLFUolAb5srZfnWqnke90Qlk/edit?tab=t.vhga5eeqazd4"))
    return ConversationHandler.END

async def handlerListingBuying_ChooseCharm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose which camera to buy,
    now is to choose which charm to get
    """
    query = update.callback_query
    await query.answer()

    queryInfo = query.data.split(" ")
    if (queryInfo[0] == "back"):
        index = queryInfo[1]
    else:
        index = queryInfo[0]
    indexCamera = listings[int(index)]
    global customerPurchaseInfos
    telegramID = update.effective_chat.id

    #check if cart is non-empty, if so, stop procedure
    customerCarts = shopping_cart.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    if userCartIndex != "NO_ITEM_FOUND":
        #cart is found and is non-empty. terminate buying procedure:
        logging.info("non-empty cart found, terminating buying procedure")
        await context.bot.send_message(chat_id=telegramID,
                                 text="There are still items in the cart, please buy cameras separately.\nFor group orders, please contact the sellers.")
        return ConversationHandler.END

    #nothing inside cart, can add into cart
    logging.info("user has cart in index " + str(userCartIndex) )

    userPurchaseInfo = PurchaseInfo(telegramID, indexCamera, "", "", "")
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex != "NO_ITEM_FOUND":
        #random/previous information is found, need to replace it
        customerPurchaseInfos.list[userIndex] == "EMPTY"

    customerPurchaseInfos.insertIntoMap(telegramID, userPurchaseInfo)

    charm_keyboard = [[InlineKeyboardButton("Plain", callback_data="Plain " + index),
                       InlineKeyboardButton("Beaded", callback_data="Beaded " + index),
                       InlineKeyboardButton('Go Back', callback_data="back " + index)]]
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

    #get purchase info
    global customerPurchaseInfos
    telegramID = update.effective_chat.id
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex == "NO_ITEM_FOUND":
        #error occured, need to redo
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unexpected exception occured. Exiting listings. Please try again.")
        return ConversationHandler.END

    #update strap choice
    queryInfo = query.data.split(" ")
    customerPurchaseInfos.list[userIndex].strapChoice = queryInfo[0]

    #set up keyboard
    addon_keyboard = [[InlineKeyboardButton("Yes (lightning cable)", callback_data="lightning " + queryInfo[1]),
                       InlineKeyboardButton("Yes(type C cable)", callback_data="type-C " + queryInfo[1])],
                       [InlineKeyboardButton("No", callback_data="no"),
                        InlineKeyboardButton("Go Back", callback_data='back ' + queryInfo[1])]]
    await query.edit_message_text(
        text="Next, would you like a SD card reader? (additional $5)\n"
            "Use /cancel at any time to stop the procedure"
        , reply_markup=InlineKeyboardMarkup(addon_keyboard)
    )
    return LISTING_BUYING_CONFIRMATION

async def handlerListingBuying_Confirmation (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose the camera and the charm and the add-ons,
    now is to confirm
    """
    query = update.callback_query
    await query.answer()

    global customerPurchaseInfos
    telegramID = update.effective_chat.id

    sdCardReaderChoice = query.data
    queryInfo = query.data.split(" ")
    sdCardReaderChoice = queryInfo[0]

    #get the userPurchaseInfo
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex == "NO_ITEM_FOUND":
        #error occured, need to redo
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unexpected exception occured. Exiting listings. Please try again.")
        return ConversationHandler.END

    #update userPurchaseInfo
    userPurchaseInfo = customerPurchaseInfos.list[userIndex]
    customerPurchaseInfos.list[userIndex].sdCardReaderChoice = sdCardReaderChoice
    customerPurchaseInfos.list[userIndex].priceAmount = userPurchaseInfo.camera.price
    if sdCardReaderChoice != "no" :
        customerPurchaseInfos.list[userIndex].priceAmount += 5

    #set up message and keyboard
    message = ("Do you want to add the camera into your cart?\n\n" +
               "Camera info:\n" +
               "==================================\n" +
               "Camera: " + userPurchaseInfo.camera.name + "\n" +
               "Strap Choice: " + userPurchaseInfo.strapChoice + "\n" +
               "SD Card Reader: " + userPurchaseInfo.sdCardReaderChoice + "\n" +
               "Total price: " + str(userPurchaseInfo.priceAmount) + "\n" +
               "==================================" + "\n" +
               "Use /cancel to stop the procedure, or press back to go back to add-on selection")
    keyboard = [[InlineKeyboardButton("Add to Cart", callback_data="yes"),
                 InlineKeyboardButton("Go Back", callback_data=sdCardReaderChoice + " " + queryInfo[1])]]

    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LISTING_BUYING_ADDEDTOCART

async def handlerListingBuying_AddedToCart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    User confirms to want this camera
    Now is to add into the user's cart
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerPurchaseInfos
    telegramID = update.effective_chat.id
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex == "NO_ITEM_FOUND":
        #error occured, need to redo
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unexpected exception occured. Exiting listings. Please try again.")
        return ConversationHandler.END
    userPurchaseInfo = customerPurchaseInfos.list[userIndex]
    #check if user has a ongoing cart
    customerCarts = shopping_cart.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    if userCartIndex == "NO_ITEM_FOUND":
        #no cart is found, need to make a new cart
        logging.info("no cart found, new cart to be made now")
        newCart = Cart(telegramID, [userPurchaseInfo])
        customerCarts.insertIntoMap(telegramID, newCart)
    else:
        #the user has a cart
        logging.info("user has cart in index " + str(userCartIndex) )
        customerCarts.list[userCartIndex].cart.append(userPurchaseInfo)

    shopping_cart.customerCarts = customerCarts
    message = ("Camera has been added into your cart!\n"
               "Please use /cart to view your shopping cart, and use /checkout to pay and confirm delivery details. :)")

    await query.edit_message_text(text=message)
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