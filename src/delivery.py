import logging
import requests
from firebase_admin.auth import InvalidDynamicLinkDomainError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

import manageorders
'''
for the buyer to fill in delivery information to proceed with the delivery
'''

DELIVERY_START, DELIVERY_ASKING_INFO = range(2)

async def delivery_start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    shows starting page for the buyer to choose
    """
    keyboard = [[InlineKeyboardButton("fill in delivery information", callback_data="info")],
                [InlineKeyboardButton("check delivery status", callback_data="status")]]

    await update.message.reply_text(text="What would you like to do today?",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY_START

def findOrder (paidOrders, id):
    i = 0
    while i < len(paidOrders):
        if paidOrders[i].id == id:
            break
        i+=1
    return i

async def delivery_fillInInfo (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    lets user fill in delivery information
    """
    query = update.callback_query
    await query.answer()

    paidOrders = manageorders.listOfPaidOrders
    i = findOrder(paidOrders, update.effective_chat.id)
    if i == len(paidOrders):
        await query.edit_message_text(text="You do not have an order with payment verified. "
                                           "Once your payment is verified, we will let you know and then you can fill in your delivery information. "
                                           "For any further enquiries, please use /FAQ or contact our sellers.")
        return ConversationHandler.END
    await query.edit_message_text(text="Your payment for your order has been verified!\n" + paidOrders[i].order + "\n\nPlease copy the following message and fill in your delivery information and send it here.")
    await context.bot.send_message(chat_id= update.effective_chat.id
                                   ,text="DELIVERY INFO:\nName:\nPostal Code:\nAddress:\nUnit No:\nContact No:")
    return DELIVERY_ASKING_INFO

async def delivery_confirmDeliveryInfo (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    confirms the delivery information, and updates the user's DeliveryInfo class
    """
    infoReceived = update.message.text.split("\n")
    paidOrders = manageorders.listOfPaidOrders
    i = findOrder(paidOrders, update.effective_chat.id)

    #fill in information
    paidOrders[i].name = (infoReceived[1].split(":"))[1].strip()
    logging.info(paidOrders[i].name)
    paidOrders[i].postalcode = (infoReceived[2].split(":"))[1].strip()
    logging.info(paidOrders[i].postalcode)
    paidOrders[i].address = (infoReceived[3].split(":"))[1].strip()
    logging.info(paidOrders[i].address)
    paidOrders[i].unitnumber = (infoReceived[4].split(":"))[1].strip()
    logging.info(paidOrders[i].unitnumber)
    paidOrders[i].contactnumber = (infoReceived[5].split(":"))[1].strip()
    logging.info(paidOrders[i].contactnumber)

    #add into deliveryOrders
    manageorders.listOfDeliveryOrders.append(paidOrders[i])
    #remove from paidOrders
    manageorders.listOfPaidOrders.pop(i)
    '''
    api_key = manageorders.api_key
    auth_key = manageorders.authentication_key

    #check rates
    domain = "http://demo.connect.easyparcel.sg/?ac="
    action = "MPRateCheckingBulk"
    url = domain + action
    postparam = {
        'authentication': auth_key,
        'api': api_key,
        'bulk': [{
            "pick_code": paidOrders[i].postalcode,
            "pick_country": "SG",
            "send_code": "510709",
            "send_country": "SG",
            "weight": 0.2
        }]
    }
    headers = {
        'Content-Type': 'application/json'
    }


    # Send the POST request
    response = requests.post(url, json=postparam, headers=headers)

    logging.info(response.json())
    '''
    await update.message.reply_text(text=("You have inputted the following:\n\n"
                                          + update.message.text +
                                          "\n\nIf this is incorrect, please message our seller @" + paidOrders[i].purchaseInfo.camera.seller.username + " as soon as possible. "))
    await context.bot.send_message(chat_id=paidOrders[i].purchaseInfo.camera.seller.id,
                                   text=("@" + paidOrders[i].username + "has submitted their delivery information. Please choose the delivery option.\n" +
                                         paidOrders[i].type + " of delivery required."))
    return ConversationHandler.END