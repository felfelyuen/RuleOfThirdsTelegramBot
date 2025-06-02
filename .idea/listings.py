import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from camera import Camera
from purchase_info import PurchaseInfo
from shopping_cart import Cart
import shopping_cart

def setUpTestListings():
    #listings = []
    cam1 = Camera("Sony", "Cybershot DSC-WX1", "yes", "", "16.1", 169, "@taylorswif")
    cam2 = Camera("Nikon", "Coolpix L1", "", "AA", "10",189,"@ethelcain")
    cam3 = Camera("Canon", "Ixy 120", "", "", "16", 299,"@wannnts")

    listings = [cam1, cam2, cam3]

    return listings

listings = setUpTestListings()


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
    indexCamera = listings[int(query.data)]
    camera_message = indexCamera.message

    new_keyboard = [[InlineKeyboardButton("Buy!", callback_data=query.data),
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

    indexCamera = listings[int(query.data)]
    global userPurchaseInfo
    userPurchaseInfo = PurchaseInfo(indexCamera, "", "", "")

    charm_keyboard = [[InlineKeyboardButton("Plain", callback_data="Plain"),
                       InlineKeyboardButton("Beaded", callback_data="Beaded"),
                       InlineKeyboardButton('Go Back', callback_data="back")]]
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
    global userPurchaseInfo
    userPurchaseInfo.strapChoice = query.data

    addon_keyboard = [[InlineKeyboardButton("Yes (lightning cable)", callback_data="lightning"),
                       InlineKeyboardButton("Yes(type C cable)", callback_data="type C")],
                       [InlineKeyboardButton("No", callback_data="no"),
                        InlineKeyboardButton("Go Back", callback_data='back')]]
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

    global userPurchaseInfo
    sdCardReaderChoice = query.data
    userPurchaseInfo.sdCardReaderChoice = sdCardReaderChoice
    userPurchaseInfo.priceAmount = userPurchaseInfo.camera.price
    if sdCardReaderChoice != "no" :
        userPurchaseInfo.priceAmount += 5

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
                 InlineKeyboardButton("Go Back", callback_data="back")]]
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
    global userPurchaseInfo

    #check if user has a ongoing cart
    customerCarts = shopping_cart.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    if userCartIndex == "NO_CART_FOUND":
        #no cart is found, need to make a new cart
        logging.info("no cart found, new cart to be made now")
        newCart = Cart(telegramID, [userPurchaseInfo])
        customerCarts.insertIntoMap(newCart)
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