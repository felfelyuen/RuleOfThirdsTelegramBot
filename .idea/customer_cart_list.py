def hashfunction (i) -> int:
    #returns the leftmost digit
    while (i % 10) != 0 :
        i /= 10
    return i

def incre(list, i):
    i += 1
    if i == len(list):
        i = 0
    return i

def insertIntoList(list, i):
    #i is the Cart of someone
    index = hashfunction(i.id)
    #inserting it now
    insertIndex = int(len(list) / 10 * index)
    while (True) :
        if ((list[insertIndex] == "EMPTY") | (list[insertIndex] == "")):
            list[insertIndex] = i
            break
        insertIndex = incre(list, i)

def expandList(list):
    newList =[len(list) * 2]
    for x in list:
        if ((x != "EMPTY") | (x != "")) :
            insertintoList(newList, x)
    return newList

def reduceList(list):
    newList =[len(list) / 2]
    for x in list:
        if ((x != "EMPTY") | (x != "")) :
            insertIntoList(newList, x)
    return newList

class Cart:
    def __init__(self, id, cart):
        self.id = id #integer
        self.cart = cart #array of cameras

class HashMap:
    def __init__(self):
        self.list = ["", "", "", "", "", "", "", "", "", ""]
        self.amount = 0

    def findCartIndex (self, id):
        #returns the index of where the cart is at
        #id must be an integer
        index = hashfunction(id)
        checkIndex = int(len(self.list) /10 * index)
        while (True) :
            if (self.list[checkIndex] == "") :
                return "NO_CART_FOUND"
            if ((self.list[checkIndex] == "EMPTY")) :
                checkIndex = incre(self.list, i)
            elif (self.list[checkIndex].id != id):
                checkIndex = incre(self.list, i)
            else :
                return checkIndex

    def insertIntoMap(self, i):
        insertIntoList(self.list, i)
        self.amount += 1
        if (self.amount == len(self.list)):
            self.list = expandList(self.list)

    def removeFromMap (self, index):
        self.list[index] = "EMPTY"
        self.amount -= 1
        if (self.amount <= len(self.list)/4):
            reduceList(self.list)





