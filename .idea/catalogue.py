import requests
import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler)
from camera import Camera

class Catalogue:
    cameras
    size

    def __init__(self):
        self.cameras = [50]
        self.size = 0

    def __add__(self, camera):
        cameras.add(camera)

async def handlerCatalogueStart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    handles start of conversation with catalogue
    """
