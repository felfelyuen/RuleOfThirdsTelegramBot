import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from camera import Camera
from purchase_info import PurchaseInfo
import delivery

class Cart:
    """
    Class for the user's shopping cart
    """
    def __init__(self, id, cart):
        self.id = id #integer
        self.cart = cart #array of purchase infos

CART_EDIT, CART_REMOVE_CONFIRM, CART_REMOVE_COMPLETE, CART_CLEAR_COMPLETE = range(4)

def printPurchaseInfo (i, info):
    message = ("==================================\n" +
               str(i + 1) + ". " + info.camera.name + "\n    " +
               info.strapChoice + " Strap\n    " +
               info.sdCardReaderChoice + " SD Card Reader\n\n    " +
               "PRICE: " + str(info.priceAmount) + "\n" +
               "==================================\n")
    return message

async def handlerCartStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Displays the shopping cart to the user.
    """
    #retrieve cart
    telegramID = update.effective_chat.id

    customerCarts = delivery.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    if userCartIndex == "NO_CART_FOUND":
        #no cart is found, need to make a new cart
        logging.info("no cart found ")
        await update.message.reply_text("Your cart is\n"
                                        " E M P T Y :)")
        return ConversationHandler.END

    #cart is found
    userCart = customerCarts.list[userCartIndex].cart
    listOfCameras = ""
    i = 0
    totalPrice = 0
    while i < len(userCart):
        indexPurchaseInfo = userCart[i]
        listOfCameras += printPurchaseInfo(i, indexPurchaseInfo) + "\n"
        totalPrice += indexPurchaseInfo.priceAmount
        i += 1
    message = ("Here is your shopping cart!\n\n" +
               listOfCameras +
               "Total Price: " +str(totalPrice) + "\n" +
               "==================================\n" +
               "use /checkout to pay")
    keyboard = [[InlineKeyboardButton("Remove item from cart", callback_data='remove')],
                [InlineKeyboardButton("Clear cart", callback_data="clear")]]
    await update.message.reply_text(text=message,
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_EDIT

async def handlerCartRemoveItem (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Asks the user which item to remove (item must be removed one at a time)
    """
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    customerCarts = delivery.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    listOfCameras = ""
    i = 0
    while i < len(userCart):
        indexPurchaseInfo = userCart[i]
        listOfCameras += printPurchaseInfo(i, indexPurchaseInfo) + "\n"
        i += 1
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
    customerCarts = delivery.customerCarts
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
    customerCarts = delivery.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart
    indexPurchaseInfo = userCart[int(query.data)]

    #remove item
    userCart.pop(int(query.data))

    #if cart has nothing, then remove cart from map
    if len(userCart) == 0:
        delivery.customerCarts.removeFromMap(userCartIndex)

    #print some message
    await query.edit_message_text(text="Camera removed!\n" + printPurchaseInfo(int(query.data), indexPurchaseInfo))
    return ConversationHandler.END

async def handlerCartClearConfirm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    customerCarts = delivery.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)
    userCart = customerCarts.list[userCartIndex].cart

    listOfCameras = ""
    i = 0
    totalPrice = 0
    while i < len(userCart):
        indexPurchaseInfo = userCart[i]
        listOfCameras += printPurchaseInfo(i, indexPurchaseInfo) + "\n"
        i += 1

    keyboard =[[InlineKeyboardButton(text="Yes", callback_data=query.data),
                InlineKeyboardButton(text="No (go back)", callback_data="back")]]

    await query.edit_message_text(text="Are you sure you want to clear the whole cart?\nCart items:\n\n" + listOfCameras,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_CLEAR_COMPLETE

async def handlerCartClearComplete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    telegramID = update.effective_chat.id
    customerCarts = delivery.customerCarts
    userCartIndex = customerCarts.findCartIndex(telegramID)

    #remove cart from hash map because it is empty now
    delivery.customerCarts.removeFromMap(userCartIndex)

    await query.edit_message_text(text="Cart cleared!")
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

