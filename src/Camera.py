class Camera:
    """
    Class for a camera and its details
    """
    def __init__(self, brand, model, japanese, battery, megapixel, price, seller):
        self.brand = brand
        self.model = model
        self.japanese = japanese
        self.battery = battery
        self.megapixel = megapixel
        self.price = price
        #seller is of the Seller (in seller_info) class
        self.seller = seller

        self.name = brand + " " + model

        #take note that this is a temporary demo message
        self.message = ("This is a " + self.name + "\n" +
                        "Price: " + str(price) + "\n" +
                        "BUY IT NOW!\n" +
                        "Contact @" + seller.username + " for more information :)")

        #queue for each camera to have, so that only one is sold at a time
        self.queue = []