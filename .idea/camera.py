class Camera:
    def __init__(self, brand, model, japanese, battery, megapixel, quantity, message):
        self.brand = brand
        self.model = model
        self.name = brand + " " + model
        self.japanese = japanese
        self.battery = battery
        self.megapixel = megapixel
        self.quantity = quantity
        self.message = message