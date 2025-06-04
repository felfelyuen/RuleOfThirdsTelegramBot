import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from camera import Camera
from purchase_info import PurchaseInfo
import listings
from HashMap import HashMap
from cart import Cart

(CART_EDIT,
 CART_REMOVE_CONFIRM, CART_REMOVE_COMPLETE,
 CART_CLEAR_COMPLETE,
 CART_PAY_CONFIRM, CART_PAY_WAITING_PAYMENT) = range(6)

global customerCarts
customerCarts = HashMap()

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

async def handlerCartStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
               "==================================\n" +
               "use /checkout to pay")
    keyboard = [#[InlineKeyboardButton("Remove item from cart", callback_data='remove')], #cart is only one item per time hence
                [InlineKeyboardButton("Clear cart", callback_data="clear")],
                [InlineKeyboardButton("Pay and checkout", callback_data="checkout")]]
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=message,
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_EDIT

'''
=========================================================================
REMOVE CART ITEM FUNCTIONS
=========================================================================
'''
async def handlerCartRemoveItem (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def handlerCartRemoveConfirm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def handlerCartRemoveComplete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def handlerCartClearConfirm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def handlerCartClearComplete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)

    #remove cart from hash map because it is empty now
    customerCarts.removeFromMap(userCartIndex)

    await query.edit_message_text(text="Cart cleared!")
    return ConversationHandler.END

'''
=========================================================================
PAY AND DELIVERY FUNCTIONS
=========================================================================
'''
async def handlerCartPayConfirmationPage (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    keyboard = [[InlineKeyboardButton("yes", callback_data="Y"),
                 InlineKeyboardButton("No (go back)", callback_data="back")]]

    await query.edit_message_text(text= message,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_PAY_CONFIRM

async def handlerCartPay_ChooseDelivery (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    keyboard = [[InlineKeyboardButton("ASAP delivery (1-2 days) ($5 more)", callback_data="ASAP")],
                [InlineKeyboardButton("normal delivery (3-5 days)", callback_data="delivery")],
                [InlineKeyboardButton("pick-up", callback_data="pick-up")]]

    #ask what delivery they want
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Please choose your delivery option:\n(Payment to be made after delivery choice is chosen)",
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_PAY_WAITING_PAYMENT

async def handlerCartPay_Pickup (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    the user wants pick-up
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    userCamera = userCart[0] #only one camera per transaction
    listOfCameras, totalPrice = printCart(userCart)

    await context.bot.send_message(chat_id=update.effective_chat.id, #replace with seller's telegram id
                                   text="pick-up for @" + update.effective_chat.username + "\nOrder:\n" + listOfCameras)

    await query.edit_message_text(text="The sellers has been notified. Please contact " + userCamera.camera.seller + "to work out the pick-up details.\n(We might not be able to message you due to your privacy settings)")

    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 caption="Additionally, send $" + str(totalPrice) + " to the number INSERTNUMBERHERE, or scan the paynow code\nScreenshot and send to " + userCamera.camera.seller + " as well.",
                                 photo=open('testpicture.png', 'rb'))
    return ConversationHandler.END

async def handlerCartPay_Delivery (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    the user wants delivery (normal)
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    userCamera = userCart[0] #only one camera per transaction
    listOfCameras, totalPrice = printCart(userCart)
    #inform sellers
    await context.bot.send_message(chat_id=update.effective_chat.id, #replace with seller's telegram id
                                   text="Normal delivery for @" + update.effective_chat.username + "\nOrder:\n" + listOfCameras)

    #tell buyers to fill in
    await query.edit_message_text(text=("The sellers has been notified. Please contact " + userCamera.camera.seller + " and send the following for delivery purposes:" +
                                         "\n(We might not be able to message you due to your privacy settings)"))
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="DELIVERY INFO:\nName:\nPostal Code:\nAddress:\nUnit No:\nContact No:")
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 caption="Additionally, send $" + str(totalPrice) + " to the number INSERTNUMBERHERE, or scan the paynow code\nScreenshot and send to " + userCamera.camera.seller + " as well.",
                                 photo=open('testpicture.png', 'rb'))
    return ConversationHandler.END

async def handlerCartPay_Asap (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    the user wants delivery (normal)
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    global customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    userCamera = userCart[0] #only one camera per transaction
    listOfCameras, totalPrice = printCart(userCart)

    totalPrice += 5
    #inform sellers
    await context.bot.send_message(chat_id=update.effective_chat.id, #replace with seller's telegram id
                                   text="ASAP delivery for @" + update.effective_chat.username + "\nOrder:\n" + listOfCameras)

    #tell buyers to fill in
    await query.edit_message_text(text=("The sellers has been notified. Please contact " + userCamera.camera.seller + " and send the following for delivery purposes:" +
                                        "\n(We might not be able to message you due to your privacy settings)"))
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="DELIVERY INFO:\nName:\nPostal Code:\nAddress:\nUnit No:\nContact No:")
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 caption=("Additionally, send $" + str(totalPrice) + " to the number INSERTNUMBERHERE, or scan the paynow code\n" +
                                          "Screenshot and send to " + userCamera.camera.seller + " as well.\n" +
                                          "Do note that delivery will not start without the screenshot."),
                                 photo=open('testpicture.png', 'rb'))
    return ConversationHandler.END

async def handlerCartCancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation if the user cancels and it will exit the conversation and the listings mode
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exited Cart"
    )
    return ConversationHandler.END

