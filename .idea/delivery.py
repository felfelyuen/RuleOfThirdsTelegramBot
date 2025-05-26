import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from camera import Camera
from purchase_info import PurchaseInfo
from customer_cart_list import HashMap
#HashMap of all the customer tele ids, and their carts.
#if the cart is cleared, the tele id is removed from the hashmap

customerCarts = HashMap()


