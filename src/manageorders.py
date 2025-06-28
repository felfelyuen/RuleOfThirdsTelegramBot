import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from DeliveryInfo import DeliveryInfo
'''
for the seller to manage orders 
'''

MANAGE_ORDER_START, MANAGE_ORDER_PAYMENT_CONFIRMATION, MANAGE_ORDER_DELIVERY_INFO_ASKED = range(3)

#demo authentication key being used
authentication_key = "n7PFeTZjRT"
api_key = "EP-GEsNV2OmJ"

listOfUnpaidOrders = []
listOfPaidOrders = []
listOfDeliveryOrders = []

async def manageOrders_Start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton("verify payment", callback_data="verify")],
                [InlineKeyboardButton("other stuff lol", callback_data="other")]]
    await update.message.reply_text(text="What do you want to do today?", reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGE_ORDER_START

'''
=========================================================================
VERIFY PAYMENT FUNCTIONS
=========================================================================
'''

async def manageOrders_verifyPayment_listCustomers (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show list of customers to verify payment for
    """
    query = update.callback_query
    await query.answer()

    global listOfUnpaidOrders
    if len(listOfUnpaidOrders) == 0:
        await query.edit_message_text(text="There are no pending orders to verify payment or to wait payment for.")
        return ConversationHandler.END

    keyboard = []
    i = 0
    while i < len(listOfUnpaidOrders):
        keyboard.append([InlineKeyboardButton(text=listOfUnpaidOrders[i].username, callback_data=str(i))])
        i += 1

    keyboard.append([InlineKeyboardButton(text="go back", callback_data="back")])
    await query.edit_message_text(text="Choose the customer to verify payment for:",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGE_ORDER_PAYMENT_CONFIRMATION

async def manageOrders_verifyPayment_Confirmation (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    shows the order, and the total required to be collected, and then asks seller again to double confirm
    """
    query = update.callback_query
    await query.answer()

    logging.info(query.data)
    index = int(query.data)
    #fetch order information
    global listOfUnpaidOrders
    indexOrder = listOfUnpaidOrders[index]
    message = ("Verify this order's payment?\n" +
               "==================================\n" +
               "Username:\n" + indexOrder.username +
               "\n\nOrder:\n" + indexOrder.order +
               "\n\nAmount to be received:\n" + str(indexOrder.total) +
               "\n==================================\n")

    keyboard = [[InlineKeyboardButton("confirm", callback_data="yes " + str(index)), InlineKeyboardButton("go back", callback_data= "back")]]

    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGE_ORDER_DELIVERY_INFO_ASKED

async def manageOrders_askCustomerForDeliveryInfo (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    sends the VERIFIED! message to the buyer, buyer prompted to use /delivery to send delivery information
    """
    query = update.callback_query
    await query.answer()

    index = int((query.data.split())[1])
    global listOfUnpaidOrders
    indexOrder = listOfUnpaidOrders[index]

    #update list of paid orders
    global listOfPaidOrders
    listOfPaidOrders.append(indexOrder)

    #tell seller
    await query.edit_message_text(text="Payment verified! Customer @" + indexOrder.username + "has been asked for their delivery information.")

    #tell buyer
    await context.bot.send_message(chat_id=indexOrder.id, text="Your payment has been verified! Please use /delivery to proceed with filling in your delivery information as soon as possible.")

    return ConversationHandler.END

'''
=========================================================================
SEND PARCEL FUNCTIONS
=========================================================================
'''

async def manageOrders_cancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    fallback for the conversation
    """
    await update.message.reply_text(text="Manage Orders exited.")
    return ConversationHandler.END