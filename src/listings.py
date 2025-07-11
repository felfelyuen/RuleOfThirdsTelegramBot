import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from Camera import Camera
from Purchase_info import PurchaseInfo
from HashMap import HashMap
import shopping_cart
from Cart import Cart
from Seller_info import Seller

def setUpTestListings():
    seller1 = Seller(796353209, "falafelyuen", "Felix Yuen", "462153", "153B Bedok South Road ","#11-402", "+6594685756")
    cam1 = Camera("Sony", "Cybershot DSC-WX1", "yes", "", "16.1", 169, seller1)
    cam2 = Camera("Nikon", "Coolpix L1", "", "AA", "10",189, seller1)
    cam3 = Camera("Canon", "Ixy 120", "", "", "16", 299, seller1)
    test_listings = [cam1, cam2, cam3]
    return test_listings

listings = setUpTestListings()

customerPurchaseInfos = HashMap()

og_message_id = ""

LISTING_START, LISTING_CHOOSE_CAMERA, LISTING_AFTERCHOSEN, LISTING_BUYING_ADDON, LISTING_BUYING_CONFIRMATION, LISTING_BUYING_ADDEDTOCART = range(6)

async def listings_Start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    global og_message_id
    if og_message_id == "":
        new_message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                                     text="Here are the listings! Click on any button to view the camera and buy!\n Use /cancel to exit the listings",
                                                     reply_markup=reply_markup)
        og_message_id = new_message.id
    else:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=og_message_id,
                                            text="Here are the listings! Click on any button to view the camera and buy!\n Use /cancel to exit the listings",
                                            reply_markup=reply_markup)

    return LISTING_CHOOSE_CAMERA

async def listings_Choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation when the user is choosing which camera to buy.
    """
    query = update.callback_query
    await query.answer()

    global listings
    queryData = query.data.split()
    if queryData[0] == "back":
        cameraIndex = queryData[1]
    else:
        cameraIndex = queryData[0]
    indexCamera = listings[int(cameraIndex)]
    camera_message = indexCamera.message

    new_keyboard = [[InlineKeyboardButton("Buy!", callback_data=cameraIndex),
                     InlineKeyboardButton("Go Back", callback_data="back"),
                     InlineKeyboardButton("Enquire about listing", callback_data="qn " + cameraIndex)]]
    await query.edit_message_text(text=camera_message, reply_markup=InlineKeyboardMarkup(new_keyboard))
    return LISTING_AFTERCHOSEN

async def listings_Enquiry (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    To handle the user's questions
    """
    query = update.callback_query
    await query.answer()

    global listings
    queryData = query.data.split()
    index = queryData[1]
    indexCamera = listings[int(index)]
    seller = indexCamera.seller

    keyboard = [[InlineKeyboardButton("back", callback_data="back " + index)]]
    await query.edit_message_text(text=("Please message the seller: @" + seller.username + " to ask your questions about this camera\.\n" +
                                        "\(We might not be able to message you due to your privacy settings\)\n\n" +
                                        "Alternatively, for general concerns, please visit the [link](https://docs.google.com/document/d/1v4ofc_tfiPyNuJWW-iOHLFUolAb5srZfnWqnke90Qlk/edit?tab=t.vhga5eeqazd4) below for our FAQ\!\n"
                                        ),
                                  parse_mode="MarkdownV2",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return LISTING_CHOOSE_CAMERA

async def timeout_checkout (context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job

    indexTeleID = job.chat_id
    #find the guy in the listings
    global listings
    for camera in listings:
        if camera.queue[0] == indexTeleID:
            #KICK HIM OUT
            logging.info("PERSON HAS TO BE REMOVED FROM QUEUE: EXCEEDED 5 MINUTES")
            await context.bot.send_message(chat_id=indexTeleID, text="Unfortunately your 5 minutes is up. :/ Please checkout within the timing next time to avoid being booted off the queue.")
            camera.queue.pop(0)
            index = customerPurchaseInfos.findCartIndex(indexTeleID)
            if index != "NO_INDEX_FOUND":
                customerPurchaseInfos.removeFromMap(index)
            cartIndex = shopping_cart.customerCarts.findCartIndex(indexTeleID)
            if cartIndex != "NO_INDEX_FOUND":
                shopping_cart.customerCarts.removeFromMap(indexTeleID)
            #inform the next person
            if len(camera.queue) != 0:
                await context.bot.send_message(chat_id=camera.queue[0], text="Congratulations! You have been moved to the front of the queue. Please checkout with the item within 5 minutes to avoid being kicked off the queue.")
            break


async def listings_Buying_ChooseCharm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose which camera to buy,
    now is to choose which charm to get
    """
    query = update.callback_query
    await query.answer()
    queryData = query.data.split(" ")
    if queryData[0] == "back":
        cameraIndex = queryData[1]
    else:
        cameraIndex = queryData[0]

    indexCamera = listings[int(cameraIndex)]
    global customerPurchaseInfos
    telegramID = update.effective_chat.id

    #check if cart is non-empty, if so, stop procedure
    customerCarts = shopping_cart.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)

    #check if cart is empty or not
    if userCartIndex != "NO_ITEM_FOUND":
        #cart is found and is non-empty. terminate buying procedure:
        logging.info("non-empty cart found, terminating buying procedure")
        await context.bot.send_message(chat_id=telegramID,
                                       text="There are still items in the cart, please buy cameras separately.\nFor group orders, please contact the sellers directly. Seller of this camera is @" + indexCamera.seller.username)
        global og_message_id
        og_message_id = ""
        return ConversationHandler.END

    #add user to queue
    if queryData[0] != "back":
        indexCamera.queue.append(telegramID)
    #check if user is at the first
    if indexCamera.queue[0] != telegramID:
        #another user is currently purchasing, cannot proceed
        logging.info("another user is purchasing, cannot proceed")
        await context.bot.send_message(chat_id=telegramID,
                                       text="Unfortunately, another user is currently purchasing this same product too. We will notify you if they are bumped off the queue. Thank you!")
        return ConversationHandler.END

    #start timer
    if queryData[0] != "back":
        logging.info("starting 5 minutes!")
        context.job_queue.run_once(timeout_checkout, 5, chat_id=telegramID, data=5)
    #nothing inside cart, can add into cart
    logging.info("can add into cart for user")
    userPurchaseInfo = PurchaseInfo(telegramID, indexCamera, "", "", "")
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex != "NO_ITEM_FOUND":
        #random/previous information is found, need to clear it
        customerPurchaseInfos.list[userIndex] = "EMPTY"

    customerPurchaseInfos.insertIntoMap(telegramID, userPurchaseInfo)

    charm_keyboard = [[InlineKeyboardButton("Plain", callback_data="Plain " + cameraIndex),
                       InlineKeyboardButton("Beaded", callback_data="Beaded " + cameraIndex),
                       InlineKeyboardButton('Go Back', callback_data="back " + cameraIndex)]]
    await query.edit_message_text(
        text="Thank you for your interest!\n"
             "Please checkout within 5 minutes or you will be bumped off the queue.\n" 
             "Please fill in the following!\n" 
             "Wrist strap variation?\n "
             "Use /cancel at any time to stop the procedure"
        , reply_markup=InlineKeyboardMarkup(charm_keyboard)
    )
    return LISTING_BUYING_ADDON

async def listings_Buying_ChooseAddOns (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        #error occurred, need to redo
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unexpected exception occurred. Exiting listings. Please try again.")
        global og_message_id
        og_message_id = ""
        return ConversationHandler.END

    #update strap choice
    queryData = query.data.split(" ")
    customerPurchaseInfos.list[userIndex].strapChoice = queryData[0]
    cameraIndex = queryData[1]

    #set up keyboard
    addon_keyboard = [[InlineKeyboardButton("Yes (lightning cable)", callback_data="lightning " + cameraIndex),
                       InlineKeyboardButton("Yes(type C cable)", callback_data="type-C " + cameraIndex)],
                       [InlineKeyboardButton("No", callback_data="no " + cameraIndex),
                        InlineKeyboardButton("Go Back", callback_data="back " + cameraIndex)]]
    await query.edit_message_text(
        text="Next, would you like a SD card reader? (additional $5)\n"
            "Use /cancel at any time to stop the procedure"
        , reply_markup=InlineKeyboardMarkup(addon_keyboard)
    )
    return LISTING_BUYING_CONFIRMATION

async def listings_Buying_Confirmation (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation after the user chose the camera and the charm and the add-ons,
    now is to confirm
    """
    query = update.callback_query
    await query.answer()

    global customerPurchaseInfos
    telegramID = update.effective_chat.id

    queryData = query.data.split(" ")
    sdCardReaderChoice = queryData[0]

    #get the userPurchaseInfo
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex == "NO_ITEM_FOUND":
        #error occurred, need to redo
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unexpected exception occurred. Exiting listings. Please try again.")
        global og_message_id
        og_message_id = ""
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
                 InlineKeyboardButton("Go Back", callback_data=userPurchaseInfo.strapChoice + " " + queryData[1])]]

    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LISTING_BUYING_ADDEDTOCART

async def listings_Buying_AddedToCart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    User confirms to want this camera
    Now is to add into the user's cart
    """
    query = update.callback_query
    await query.answer()
    global og_message_id

    #get the userPurchaseInfo
    global customerPurchaseInfos
    telegramID = update.effective_chat.id
    userIndex = customerPurchaseInfos.findCartIndex(telegramID)
    if userIndex == "NO_ITEM_FOUND":
        #error occurred, need to redo
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unexpected exception occurred. Exiting listings. Please try again.")
        og_message_id = ""
        return ConversationHandler.END
    userPurchaseInfo = customerPurchaseInfos.list[userIndex]

    #check if user has an ongoing cart
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

    #remove customer's purchase info from list

    customerPurchaseInfos.removeFromMap(userIndex)
    message = ("Camera has been added into your cart!\n"
               "Please use /cart to view your shopping cart and checkout to pay. :)")

    await query.edit_message_text(text=message)
    og_message_id = ""
    return ConversationHandler.END

async def listings_Fallback (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation if the user cancels, and it will exit the conversation and the listings mode
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exited Catalogue mode"
    )
    #reset og_message_id
    global og_message_id
    og_message_id = ""

    return ConversationHandler.END