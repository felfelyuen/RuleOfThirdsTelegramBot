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

CART_EDIT = range(1)

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
        listOfCameras += ("==================================\n" +
                          str(i) + ". " + indexPurchaseInfo.camera.name + "\n    " +
                          indexPurchaseInfo.strapChoice + " Strap\n    " +
                          indexPurchaseInfo.sdCardReaderChoice + " SD Card Reader\n\n    " +
                          "PRICE:" + str(indexPurchaseInfo.priceAmount) + "\n\n")
        totalPrice += indexPurchaseInfo.priceAmount
        i += 1
    message = ("Here is your shopping cart!\n\n" +
               listOfCameras +
               "==================================\n" +
               "Total Price: " +str(totalPrice) + "\n" +
               "==================================\n" +
               "use /checkout to pay")
    keyboard = [[InlineKeyboardButton("Remove item from cart", callback_data='remove')],
                [InlineKeyboardButton("Clear cart", callback_data="clear")]]
    await update.message.reply_text(text=message,
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return CART_EDIT

async def handlerCartCancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the conversation if the user cancels and it will exit the conversation and the listings mode
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exited Cart"
    )
    return ConversationHandler.END

