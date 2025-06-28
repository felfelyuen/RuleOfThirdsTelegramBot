class PurchaseInfo:
    def __init__(self, id, camera, strapChoice, sdCardReaderChoice, priceAmount):
        self.id = id
        #camera is of the Camera class
        self.camera = camera
        self.strapChoice = strapChoice
        self.sdCardReaderChoice = sdCardReaderChoice
        self.priceAmount = priceAmount
