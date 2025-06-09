import logging
from multiprocessing.connection import address_type

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

'''
for the seller to manage orders 
'''

MANAGE_ORDER_START, ALLOW_DELIVERY_CONFIRMATION = range(2)

class DeliveryInfo:
    def __init__(self):
        self.id = iden
        self.username = username
        self.name = name
        self.postalcode = postalcode
        self.address = address
        self.unitnumber = unitnumber
        self.contactnumber = contactnumber

async def manageOrders_Start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton("ask for delivery details", callback_data="delivery")],
                [InlineKeyboardButton("otherstuff lol", callback_data="other")]]
    await update.message.reply_text(text="What do you want to do today?", reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGE_ORDER_START

async def manageOrders_ConfirmDelivery (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
