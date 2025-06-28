class DeliveryInfo:
    def __init__(self, id, username, name, postalcode, address, unitnumber, contactnumber, type, order, purchaseInfo, total):
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