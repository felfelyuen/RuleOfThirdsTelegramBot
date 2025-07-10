def hashfunction (i) -> int:
    #returns the leftmost digit
    number = str(i)
    return int(number[0])


def incre(map_list, i):
    i += 1
    if i == len(map_list):
        i = 0
    return i

def insertIntoList(map_list, iden, item):
    #item is the Cart of someone
    index = hashfunction(iden)
    #inserting it now
    insertIndex = int(len(map_list) / 10 * index)
    while True:
        if (map_list[insertIndex] == "EMPTY") | (map_list[insertIndex] == ""):
            map_list[insertIndex] = item
            break
        insertIndex = incre(map_list, insertIndex)

def expandList(map_list):
    newList =[len(map_list) * 2]
    for x in map_list:
        if (x != "EMPTY") | (x != ""):
            insertIntoList(newList, x.id, x)
    return newList

def reduceList(map_list):
    newList =[len(map_list) / 2]
    for x in map_list:
        if (x != "EMPTY") & (x != ""):
            insertIntoList(newList, x.id, x)
    return newList

class HashMap:
    """
    Class for the list of all the user's shopping cart.
    """
    def __init__(self):
        self.list = ["", "", "", "", "", "", "", "", "", ""]
        self.amount = 0

    def findCartIndex (self, iden):
        #returns the index of where the cart is at
        #id must be an integer
        index = hashfunction(iden)
        checkIndex = int(len(self.list) /10 * index)
        while True:
            if self.list[checkIndex] == "":
                return "NO_ITEM_FOUND"
            if self.list[checkIndex] == "EMPTY":
                checkIndex = incre(self.list, checkIndex)
            elif self.list[checkIndex].id != iden:
                checkIndex = incre(self.list, checkIndex)
            else :
                return checkIndex

    def insertIntoMap(self, iden, item):
        insertIntoList(self.list, iden, item)
        self.amount += 1
        if self.amount == len(self.list):
            self.list = expandList(self.list)

    def removeFromMap (self, index):
        self.list[index] = "EMPTY"
        self.amount -= 1
        if self.amount <= len(self.list)/4:
            reduceList(self.list)





