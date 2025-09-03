import logging
import requests
from pycparser.ply.yacc import resultlimit
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

'''
for the seller to manage orders 
'''

#following lines for testing only
from DeliveryInfo import DeliveryInfo
from Camera import Camera
from Seller_info import Seller
from Purchase_info import PurchaseInfo

def setUpTestDeliveryOrders ():
    seller1 = Seller(796353209, "falafelyuen", "Felix Yuen", "462153", "153B Bedok South Road ","#11-402", "+6594685756")
    cam1 = Camera("Sony", "Cybershot DSC-WX1", "yes", "", "16.1", 169, seller1)
    purchase1 = PurchaseInfo(796353209, cam1, "plain", "no", 174)
    delivery1 = DeliveryInfo(796353209, "falafelyuen", "Felix Yuen Pin Qi", "510709", "Blk 709 Pasir Ris Road", "#08-103", "+6592305493", "asap", "", purchase1, 174, "", "")
    return delivery1
#end of test code


(MANAGEORDER_START,
 MANAGEORDER_PAYMENT_CONFIRMATION, MANAGEORDER_PAYMENT_DELIVERYINFOASKED,
 MANAGE_ORDER_DELIVERY_CHOOSECOURIER, MANAGEORDER_DELIVERY_REQUEST_CONFIRMATION, MANAGEORDER_DELIVERY_MAKEORDER) = range(6)

#demo authentication key being used
auth_key = "n7PFeTZjRT"
api_key = "EP-GEsNV2OmJ"
#demo website being used
domain = 'http://demo.connect.easyparcel.sg/?ac='

#listOfUnpaidOrders is the list of orders that has been pending payment verification.
#It is dependent on the sellers to confirm if the buyer has paid the payment, on their end through their bank accounts.
listOfUnpaidOrders = []

#listOfPaidOrders is the list of orders that has payment verified, pending delivery information from the buyer.
listOfPaidOrders = []

#listOfDeliveryOrders is the list of orders that has delivery information received, waiting for the seller to choose the delivery option through EasyParcel API.
listOfDeliveryOrders = [setUpTestDeliveryOrders()]

#listOfShippedOrders is the list of orders that has had the EasyParcel order made, and is currently being sent to the customer.
listOfShippedOrders = []

#listOfRates is the list of rates obtained from querying EasyParcel
listOfRates = []

og_message_id=""

async def manageOrders_Start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton("verify payment", callback_data="verify")],
                [InlineKeyboardButton("send parcel to customer", callback_data="send")]]

    global og_message_id
    if og_message_id == "":
        newMessage = await context.bot.send_message(chat_id= update.effective_chat.id,
                                                    text="What do you want to do today?",
                                                    reply_markup=InlineKeyboardMarkup(keyboard))
        og_message_id = newMessage.message_id
    else:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=og_message_id,
                                            text="What do you want to do today?",
                                            reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGEORDER_START

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

    #no unpaid orders
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
    return MANAGEORDER_PAYMENT_CONFIRMATION

async def manageOrders_verifyPayment_Confirmation (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    shows the order, and the total required to be collected, and then asks seller again to double confirm
    """
    query = update.callback_query
    await query.answer()

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
    return MANAGEORDER_PAYMENT_DELIVERYINFOASKED

async def manageOrders_askCustomerForDeliveryInfo (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    sends the VERIFIED! message to the buyer, buyer prompted to use /delivery to send delivery information
    """
    query = update.callback_query
    await query.answer()

    index = int((query.data.split())[1])
    global listOfUnpaidOrders
    indexOrder = listOfUnpaidOrders[index]

    #update list of paid orders and unpaid orders
    global listOfPaidOrders
    listOfPaidOrders.append(indexOrder)
    listOfUnpaidOrders.pop(index)

    #tell seller
    await query.edit_message_text(text="Payment verified! Customer @" + indexOrder.username + " has been asked for their delivery information.")

    #tell buyer
    await context.bot.send_message(chat_id=indexOrder.id, text="Your payment has been verified! Please use /delivery to proceed with filling in your delivery information as soon as possible.")

    global og_message_id
    og_message_id = ""
    return ConversationHandler.END

'''
=========================================================================
SEND PARCEL FUNCTIONS
=========================================================================
'''

async def manageOrders_sendParcel_listCustomers (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    lists all the customers that have submitted their delivery information.
    """
    query = update.callback_query
    await query.answer()

    global listOfDeliveryOrders

    #check if there are orders to send for
    if len(listOfDeliveryOrders) == 0:
        await query.edit_message_text(text="There are no pending orders to send the parcel for.")
        return ConversationHandler.END

    keyboard = []
    i = 0
    while i < len(listOfDeliveryOrders):
        keyboard.append([InlineKeyboardButton(text=listOfDeliveryOrders[i].username, callback_data=str(i))])
        i += 1
    keyboard.append([InlineKeyboardButton(text="go back", callback_data="back")])

    await query.edit_message_text(text="NOTE: Dropoff orders cannot be placed through the bot.\nChoose the customer to send the parcel for:",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGE_ORDER_DELIVERY_CHOOSECOURIER

async def manageOrders_sendParcel_getRate_listCouriers (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    lists all the couriers available for that parcel order
    """
    query = update.callback_query
    await query.answer()
    data = query.data.split()
    global listOfRates

    if data[0] == "back":
        customerIndex = int(data[1])
        res = listOfRates
    else:
        customerIndex = int(data[0])
        global api_key
        global auth_key
        global listOfDeliveryOrders

        await query.edit_message_text(text="Loading... please hold on")

        #check rates
        global domain
        action = "MPRateCheckingBulk"
        url = domain + action
        postparam = {
            'authentication': auth_key,
            'api': api_key,
            'bulk': [{
                "pick_code": listOfDeliveryOrders[customerIndex].purchaseInfo.camera.seller.postalcode,
                "pick_country": "SG",
                "send_code": listOfDeliveryOrders[customerIndex].postalcode,
                "send_country": "SG",
                "weight": 0.2
            }]
        }
        headers = {
            'Content-Type': 'application/json'
        }
        # Send the POST request
        res = requests.post(url, json=postparam, headers=headers)
        logging.info(res)
        res = res.json()
        logging.info("Outcome of get_Rate API call:" + res["api_status"])

        #handle non-success api response
        if res["error_code"] != "0":
            await query.edit_message_text(text=res["error_remark"] + "Terminating procedure")
            return ConversationHandler.END

        #set listOfRates to be response
        listOfRates = res

    #set up keyboard
    keyboard = []
    i = 0
    while i < len(res["result"][0]["rates"]):
        keyboard.append([InlineKeyboardButton(text=res["result"][0]["rates"][i]["courier_name"], callback_data=str(customerIndex) + " " + str(i))])
        i += 1

    keyboard.append([InlineKeyboardButton(text="go back", callback_data="back")])
    await query.edit_message_text(text="Choose the delivery option to send the parcel for:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGEORDER_DELIVERY_REQUEST_CONFIRMATION

def filterByPostalCode (rate, seller_poscode):
    """
    filters out the dropoff points by postal code.
    :param rate: the rate, a single item found in the array of "rates"
    :param seller_poscode: the seller's postal code
    :return: result, the array of dropoff points as dictionaries (array of dictionaries)
             message, the full message containing all the dropoff points but as a message (a string)
             message_array, an array of the full message, split by each dropoff point (array of strings)
    """

    result = []
    message = ""
    message_array = []
    dropoffs = rate["dropoff_point"]
    for x in dropoffs:
        if (x["point_postcode"])[0:2] == seller_poscode[0:2] :
            #near enough to the seller
            result.append(x)
            new_message = x["point_addr1"] + " " + x["point_addr2"] + " " + x["point_addr3"] + " " + x["point_addr4"] + " " + x["point_postcode"] + " \n"
            message += new_message
            message_array.append(new_message)
    return result, message, message_array


async def manageOrders_sendParcel_getRate_confirmation (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    asks seller to confirm the courier, with a list of some possible drop-off points
    """
    query = update.callback_query
    await query.answer()

    queryData = query.data.split()
    customerIndex = int(queryData[0])
    courier_index = int(queryData[1])

    global listOfRates
    courier_info = listOfRates["result"][0]["rates"][courier_index]

    #form message
    message = "Are you sure you want to use this courier?\n\n" + "Courier information:\n"
    message += "Name: " + courier_info["courier_name"] + "\n"
    message += "Pick-up date: " + courier_info["pickup_date"] + "\n"
    message += "Delivery: " + courier_info["delivery"] + "\n"
    message += "Price of delivery: " + courier_info["price"] + "\n"
    message += "Add-on price: " + courier_info["addon_price"] + "\n"
    message += "Shipment price: " + courier_info["shipment_price"] + "\n"
    message += "Shipment tax: " + courier_info["shipment_tax"] + "\n"
    message += "Service name: " + courier_info["service_name"]

    #get seller postal code
    global listOfDeliveryOrders
    seller_poscode =  listOfDeliveryOrders[customerIndex].purchaseInfo.camera.seller.postalcode

    #get possible postal codes:
    result, message_new, message_array = filterByPostalCode(courier_info, seller_poscode)
    if len(message_array) != 0:
        message += "\n\nPossible drop-off points near you (@" + update.effective_chat.username + " ):\n"
        i = 0
        while (i < 7) & (i < len(message_array)):
            message += message_array[i]
            i += 1

    keyboard = [[InlineKeyboardButton("confirm (make order)", callback_data= query.data)],
                [InlineKeyboardButton("back", callback_data="back " + str(customerIndex))]]
    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    return MANAGEORDER_DELIVERY_MAKEORDER

async def manageOrders_sendParcel_makeOrder (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    makes order after confirmation
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(text="Loading... please hold on")

    queryData = query.data.split()
    customerIndex = int(queryData[0])
    courier_index = int(queryData[1])

    global api_key
    global auth_key
    global listOfDeliveryOrders
    global listOfRates

    indexOrder = listOfDeliveryOrders[customerIndex]
    #call makeOrder API
    global domain
    action = "MPSubmitOrderBulk"
    url = domain + action
    postparam = {
        'authentication': auth_key,
        'api': api_key,
        'bulk': [{
            "weight": 0.2,
            "content": indexOrder.purchaseInfo.camera.name,
            'value': 180,
            "service_id": listOfRates["result"][0]["rates"][courier_index]["service_id"],
            "pick_name": indexOrder.purchaseInfo.camera.seller.name,
            "pick_contact": indexOrder.purchaseInfo.camera.seller.contactnumber,
            "pick_unit": indexOrder.purchaseInfo.camera.seller.unitnumber,
            "pick_code": indexOrder.purchaseInfo.camera.seller.postalcode,
            "pick_country": "SG",
            "send_name": indexOrder.name,
            "send_contact": indexOrder.contactnumber,
            "send_unit": indexOrder.unitnumber,
            "send_addr1": indexOrder.address,
            "send_state": "png",
            "send_code": indexOrder.postalcode,
            "send_country": "SG",
        }]
    }
    headers = {
        'Content-Type': 'application/json'
    }
    # Send the POST request
    res = requests.post(url, json=postparam, headers=headers)
    res = res.json()
    logging.info("Outcome of send_Parcel API call:" + res["api_status"])

    #handle non-success api response
    if res["error_code"] != "0":
        await query.edit_message_text(text="Error found:\n" + res["error_remark"] + "\nTerminating procedure")
        return ConversationHandler.END

    await query.edit_message_text(text=res["result"][0]["remarks"])
    rates_result = res["result"][0]
    logging.info(rates_result["status"] + rates_result["remarks"])

    #check success of order
    if rates_result["status"] == "fail":
        #failed
        await query.edit_message_text(text="Placing the order has failed because of the following reason.\n\n" +
                                           rates_result["remarks"] +
                                           "\n\nPlease place the order manually, or select another delivery service. This delivery order will be removed from the database.\n Order information:\n"
                                           + indexOrder.printInfo())
        return ConversationHandler.END

    #success
    order_number = rates_result["order_number"]
    order_price = str(rates_result["price"])
    logging.info("order_number is [" + order_number + "] and order price is [" + order_price + "]")
    listOfDeliveryOrders[customerIndex].EP_order_no = order_number
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Order has been placed!\n" +
                                        rates_result["remarks"] +
                                        "\nOrder number: " + order_number + "\nOrder price: " + order_price)

    #call MakePayment API
    payment_message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                                     text="Now making payment. Please wait...")
    action_2 = "MPPayOrderBulk"
    url_2 = domain + action_2
    postparam_2 = {
        'authentication': auth_key,
        'api': api_key,
        'bulk': [{
            "order_no": order_number
        }]
    }
    res_2 = requests.post(url_2, json=postparam_2, headers=headers)
    res_2 = res_2.json()
    logging.info(res_2)

    #handle non-success api response
    if res["error_code"] != "0":
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=payment_message.message_id,
                                            text=res["error_remark"] + "Terminating procedure")
        return ConversationHandler.END

    payment_result = res_2["result"][0]

    #handle insufficient credit
    if payment_result["messagenow"] != "Sufficient credit":
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=payment_message.message_id,
                                            text="Payment did not go through due to the following error:\n" + payment_result["messagenow"])
        return ConversationHandler.END

    #successful payment
    listOfDeliveryOrders[customerIndex].EP_awb_no = payment_result["parcel"][0]["awb"]
    messageToSeller = ("Payment has been made!\n" +
                       "Order Information:\n" +
                       "Order number: " + payment_result["orderno"] +
                       "\nStatus: " + payment_result["messagenow"] +
                       "\nParcel number: " + payment_result["parcel"][0]["parcelno"] +
                       "\nAirway bill number: " + payment_result["parcel"][0]["awb"] +
                       "\nAirway bill ID link: " + payment_result["parcel"][0]["awb_id_link"])
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=payment_message.message_id,
                                        text=messageToSeller)

    global og_message_id
    og_message_id = ""
    return ConversationHandler.END

async def manageOrders_cancel (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    fallback for the conversation
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Manage Orders exited.")

    global og_message_id
    og_message_id = ""
    return ConversationHandler.END