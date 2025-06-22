class Camera:
    def __init__(self, brand, model, japanese, battery, megapixel, price, seller):
        self.brand = brand
        self.model = model
        self.japanese = japanese
        self.battery = battery
        self.megapixel = megapixel
        self.price = price
        self.seller = seller

        self.name = brand + " " + model
        self.message = ("This is a " + self.name + "\n" +
                        "Price: " + str(price) + "\n" +
                        "BUY IT NOW!\n" +
                        "Contact " + seller + " for more information :)")
