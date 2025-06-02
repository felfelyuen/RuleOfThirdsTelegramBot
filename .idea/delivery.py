
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from camera import Camera
from purchase_info import PurchaseInfo
from customer_cart_list import HashMap
#from shopping_cart import printPurchaseInfo, printCart

#HashMap of all the customer tele ids, and their carts.
#if the cart is cleared, the tele id is removed from the hashmap

customerCarts = HashMap()

async def handlerCheckoutStart (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Shows cart, before seeing if the user wants to pay or not
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
    listOfCameras, totalPrice = printCart(userCart)






#IDK WE MIGHT NOT NEED THIS
#CHECK WITH BOSS, IF DONT WANT SEPARATE /CHECKOUT FUNCTION, THEN WE DELETE THIS FILE COMPLETELY