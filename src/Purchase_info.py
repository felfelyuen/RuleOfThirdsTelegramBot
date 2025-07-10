class PurchaseInfo:
    """
    Class for the user's purchase info when using the listings.
    """
    def __init__(self, id, camera, strapChoice, sdCardReaderChoice, priceAmount):
        self.id = id
        #camera is of the Camera class
        self.camera = camera
        self.strapChoice = strapChoice
        self.sdCardReaderChoice = sdCardReaderChoice
        self.priceAmount = priceAmount
