class DeliveryInfo:
    def __init__(self, id, username, name, postalcode, address, unitnumber, contactnumber, type, order, purchaseInfo, total, EP_order_no, EP_awb_no):
        self.id = id
        self.username = username
        self.name = name
        self.postalcode = postalcode
        self.address = address
        self.unitnumber = unitnumber
        self.contactnumber = contactnumber
        self.type = type
        self.order = order
        #purchaseInfo attribute should be of the purchaseInfo class
        self.purchaseInfo = purchaseInfo
        self.total = total

        #following to be filled in after order is paid on easyparcel
        self.EP_order_no = EP_order_no
        self.EP_awb_no = EP_awb_no

    def printInfo (self):
        message = "username: " + self.username + "\n"
        message += "name: " + self.name + "\n"
        message += "postalcode: " + self.postalcode + "\n"
        message += "address: " + self.address + "\n"
        message += "unitnumber: " + self.unitnumber + "\n"
        message += "contactnumber: " + self.contactnumber + "\n"
        message += "type: " + self.type + "\n"
        message += "order: " + self.order + "\n"
        return message