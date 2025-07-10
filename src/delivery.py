import logging
from firebase_admin.auth import InvalidDynamicLinkDomainError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from HashMap import HashMap
import manageorders
'''
for the buyer to fill in delivery information to proceed with the delivery
'''

DELIVERY_START, DELIVERY_ASKING_INFO, DELIVERY_CONFIRMATION = range(3)

async def delivery_start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    shows starting page for the buyer to choose
    """
    keyboard = [[InlineKeyboardButton("fill in delivery information", callback_data="info")]
                #,[InlineKeyboardButton("check delivery status", callback_data="status")]
                ]

    await update.message.reply_text(text="What would you like to do today?",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY_START

def findOrder (paid_orders, iden):
    i = 0
    while i < len(paid_orders):
        if paid_orders[i].id == iden:
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
    asks user to confirm the delivery information
    """
    infoReceived = update.message.text.split("\n")
    telegramID = update.effective_chat.id
    paidOrders = manageorders.listOfPaidOrders
    i = findOrder(paidOrders, update.effective_chat.id)

    #fill in information
    paidOrders[i].name = (infoReceived[1].split(":"))[1].strip()
    paidOrders[i].postalcode = (infoReceived[2].split(":"))[1].strip()
    paidOrders[i].address = (infoReceived[3].split(":"))[1].strip()
    paidOrders[i].unitnumber = (infoReceived[4].split(":"))[1].strip()
    buyer_contact = (infoReceived[5].split(":"))[1].strip()
    if buyer_contact[0] != "+":
        #will assume the buyer is using singaporean contact "+65", unless explicitly stated by buyer with "+"
        buyer_contact = "+65" + buyer_contact
    paidOrders[i].contactnumber = buyer_contact

    #set paidOrders as it
    manageorders.listOfPaidOrders = paidOrders

    #set up keyboard
    keyboard = [[InlineKeyboardButton("confirm", callback_data="yes " + str(i)), InlineKeyboardButton("no (go back)", callback_data="no")]]
    await update.message.reply_text(text=("You have inputted the following:\n\n"
                                          + update.message.text + "\n\nPlease confirm if the information is accurate."),
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY_CONFIRMATION


async def delivery_DeliveryInfoComplete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    confirms the delivery information, and updates the user's DeliveryInfo class
    """
    query = update.callback_query
    await query.answer()

    paidOrders = manageorders.listOfPaidOrders
    index = int((query.data.split())[1])
    customerDeliveryInfo = manageorders.listOfPaidOrders[index]

    #add into deliveryOrders
    manageorders.listOfDeliveryOrders.append(customerDeliveryInfo)
    #remove from paidOrders
    manageorders.listOfPaidOrders.pop(index)

    await query.edit_message_text(text=("Delivery information has been sent! Please wait patiently for your order! If the delivery information is still incorrect, please message our seller @" + customerDeliveryInfo.purchaseInfo.camera.seller.username + " as soon as possible. "))
    await context.bot.send_message(chat_id=customerDeliveryInfo.purchaseInfo.camera.seller.id,
                                   text=("@" + customerDeliveryInfo.username + " has submitted their delivery information. Please use /manageorders and choose the delivery option.\n" +
                                         customerDeliveryInfo.delivery_type + " delivery required."))
    return ConversationHandler.END

