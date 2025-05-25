class Camera:
    def __init__(self, brand, model, japanese, battery, megapixel, quantity, price, message):
        self.brand = brand
        self.model = model
        self.japanese = japanese
        self.battery = battery
        self.megapixel = megapixel
        self.quantity = quantity
        self.price = price
        self.message = message

        self.name = brand + " " + model