import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
import listings
from HashMap import HashMap
import manageorders
from DeliveryInfo import DeliveryInfo

(CART_EDIT,
 CART_REMOVE_CONFIRM, CART_REMOVE_COMPLETE,
 CART_CLEAR_COMPLETE,
 CART_PAY_CONFIRM, CART_PAY_WAITING_PAYMENT) = range(6)

customerCarts = HashMap()
#pendingPaymentCustomersList = []

def printPurchaseInfo (i, info):
    message = ("==================================\n" +
               str(i + 1) + ". " + info.camera.name + "\n    " +
               info.strapChoice + " Strap\n    " +
               info.sdCardReaderChoice + " SD Card Reader\n\n    " +
               "PRICE: " + str(info.priceAmount) + "\n" +
               "==================================\n")
    return message

def printCart (cart):
    listOfCameras = ""
    i = 0
    totalPrice = 0
    while i < len(cart):
        indexPurchaseInfo = cart[i]
        listOfCameras += printPurchaseInfo(i, indexPurchaseInfo) + "\n"
        totalPrice += indexPurchaseInfo.priceAmount
        i += 1
    return listOfCameras, totalPrice

async def cart_Start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Displays the shopping cart to the user.
    """
    #retrieve cart
    telegramID = update.effective_chat.id

    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    if userCartIndex == "NO_ITEM_FOUND":
        #no cart is found, need to make a new cart
        logging.info("no cart found")
        await update.message.reply_text("Your cart is\n"
                                        " E M P T Y :)")
        return ConversationHandler.END

    #cart is found
    userCart = customerCarts.list[userCartIndex].cart
    listOfCameras, totalPrice = printCart(userCart)

    message = ("Here is your shopping cart!\n\n" +
               listOfCameras +
               "Total Price: " +str(totalPrice) + "\n" +
               "==================================\n")
    keyboard = [[InlineKeyboardButton("Pay and checkout", callback_data="checkout")],
                [InlineKeyboardButton("Clear cart", callback_data="clear")]
                #,[InlineKeyboardButton("Remove item from cart", callback_data='remove')] #cart is only one item per time hence this line is commented out
                ]
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=message,
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_EDIT

'''
=========================================================================
REMOVE CART ITEM FUNCTIONS
=========================================================================
'''
async def cart_RemoveItem (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Asks the user which item to remove (item must be removed one at a time)
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    listOfCameras, totalPrice = printCart(userCart)
    message = ("Which camera do you want to remove?\n\n" +
               listOfCameras)
    keyboard = []
    i = 0
    while i < len(userCart):
        keyboard.append([InlineKeyboardButton(text=str(i + 1), callback_data=i)])
        i += 1

    await query.edit_message_text(text= message,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_REMOVE_CONFIRM

async def cart_Remove_Confirm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Asks the user to confirm removal of that camera
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart
    indexPurchaseInfo = userCart[int(query.data)]

    userPurchaseInfoMessage = printPurchaseInfo(int(query.data), indexPurchaseInfo)


    keyboard =[[InlineKeyboardButton(text="Yes", callback_data=query.data),
                InlineKeyboardButton(text="No (go back)", callback_data="back")]]

    await query.edit_message_text(text="Do you really want to remove this camera?\n\n" + userPurchaseInfoMessage,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_REMOVE_COMPLETE

async def cart_Remove_Complete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart
    indexPurchaseInfo = userCart[int(query.data)]

    #remove item
    customerCarts.list[userCartIndex].cart.pop(int(query.data))

    #if cart has nothing, then remove cart from map
    if len(userCart) == 0:
        customerCarts.removeFromMap(userCartIndex)

    #print some message
    await query.edit_message_text(text="Camera removed!\n" + printPurchaseInfo(int(query.data), indexPurchaseInfo))
    return ConversationHandler.END

'''
=========================================================================
CLEAR CART FUNCTIONS
=========================================================================
'''

async def cart_Clear_Confirm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Asks user to confirm clearing their cart
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    listOfCameras, totalPrice = printCart(userCart)

    keyboard =[[InlineKeyboardButton(text="Yes", callback_data=query.data),
                InlineKeyboardButton(text="No (go back)", callback_data="back")]]

    await query.edit_message_text(text="Are you sure you want to clear the whole cart?\nCart items:\n\n" + listOfCameras + "\n\n Total price: " + str(totalPrice),
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_CLEAR_COMPLETE

async def cart_Clear_Complete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Clears the cart for the buyer.
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)



    #let other people in the queue know:
    userCart = customerCarts.list[userCartIndex].cart
    indexCamera = userCart[0].camera
    indexCamera.queue.pop(0)
    i = 0
    logging.info("user exited queue, informing next person in queue")
    await context.bot.send_message(chat_id=indexCamera.queue[0], text="Good News! You have been bumped to the front of the queue for the camera \"" + indexCamera.name + "\". Please place an order and checkout within 5 minutes, or else you will be removed from the queue.")

    #remove cart from hash map because it is empty now
    customerCarts.removeFromMap(userCartIndex)

    await query.edit_message_text(text="Cart cleared!")
    return ConversationHandler.END

'''
=========================================================================
PAY AND DELIVERY FUNCTIONS
=========================================================================
'''
async def cart_Pay_Confirm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Asks user to confirm payment
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    listOfCameras, totalPrice = printCart(userCart)
    message = ("Please confirm order before proceeding with checkout :)\n\n" +
               listOfCameras + "\n" +
               "Total price: " + str(totalPrice))
    keyboard = [[InlineKeyboardButton("Yes", callback_data="Y"),
                 InlineKeyboardButton("No (go back)", callback_data="back")]]

    await query.edit_message_text(text= message,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_PAY_CONFIRM

async def cart_Pay_ChooseDelivery (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    sends message asking to paynow to this phone number
    and then asks them if they want delivery
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    listOfCameras, totalPrice = printCart(userCart)

    #REMOVE LISTING
    indexCamera = userCart[0].camera
    #let other people in the queue know
    indexCamera.queue.pop(0) #remove the first person(the current buyer)
    for teleID in indexCamera.queue:
        await context.bot.send_message(chat_id=teleID, text="Unfortunately, someone else has bought the camera \"" + indexCamera.name + "\". :/")
    #remove listing fr
    i = 0
    while i < len(listings.listings):
        if listings.listings[i].name == indexCamera.name:
            logging.info(indexCamera.name + "removed")
            listings.listings.pop(i)
            break
        i += 1

    #show order confirmation
    first_message = ("Order Confirmed:\n\n" +
                     listOfCameras)
    await query.edit_message_text(text=first_message)

    keyboard = [[InlineKeyboardButton("ASAP delivery (1-2 days) ($5 more)", callback_data="ASAP delivery")],
                [InlineKeyboardButton("normal delivery (3-5 days)", callback_data="normal delivery")],
                [InlineKeyboardButton("pick-up", callback_data="pick-up")]]


    #ask what delivery they want
    new_message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Please choose your delivery option:\n(Payment to be made after delivery choice is chosen)",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_PAY_WAITING_PAYMENT

async def cart_Pay_Generic (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    userCamera = userCart[0] #only one camera per transaction
    listOfCameras, totalPrice = printCart(userCart)

    #inform sellers
    newDeliveryInfo = DeliveryInfo(telegramID, update.effective_chat.username, "", "", "", "", "", query.data, listOfCameras, userCamera, totalPrice, "", "")
    manageorders.listOfUnpaidOrders.append(newDeliveryInfo)

    await context.bot.send_message(chat_id=userCamera.camera.seller.id, #replace with seller's telegram id
                                   text=query.data + " for @" + update.effective_chat.username + "\nOrder:\n" + listOfCameras)

    #inform buyers
    if query.data == "pick-up":
        await query.edit_message_text(text="The sellers has been notified. Please contact @" +
                                           userCamera.camera.seller.username +
                                           "to work out the pick-up details.\n(We might not be able to message you due to your privacy settings)")
        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                     caption="Additionally, send $" + str(totalPrice) + " to the number " + userCamera.camera.seller.contactnumber +
                                             ", or scan the paynow code\nScreenshot and send to " + userCamera.camera.seller.username + " as well.",
                                     photo=open('../.idea/testpicture.png', 'rb'))
    else:
        if query.data == "ASAP delivery":
            totalPrice += 5

        with open('../.idea/testpicture.png', 'rb') as photo_file:
            newPhoto = InputMediaPhoto(media=photo_file, caption="The sellers have been notified, please paynow $" + str(totalPrice) + " to the number " + userCamera.camera.seller.contactnumber + ", or scan the paynow code.\n" +
                                                                     "Screenshot proof of payment and send it to @" + userCamera.camera.seller.username + "\n" +
                                                                     "Delivery information will be processed after payment is verified.")
        await query.edit_message_media(media=newPhoto)

    #remove cart
    customerCarts.removeFromMap(userCartIndex)
    return ConversationHandler.END

async def handlerCartCancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation if the user cancels, and it will exit the conversation and the listings mode
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exited Cart"
    )
    return ConversationHandler.END

