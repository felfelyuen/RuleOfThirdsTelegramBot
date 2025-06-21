import re
from firebase_config import db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from telegram import InputMediaPhoto, InputMediaVideo


ADD_ID, ADD_BRAND, ADD_MODEL, ADD_JAPANESE, ADD_BATTERY, ADD_MEGAPIXEL, ADD_IMAGE1, ADD_IMAGE2, ADD_VIDEO = range (9)
EDIT_SELECT_FIELD, EDIT_INPUT_VALUE = range(2)
CONFIRM_REMOVE, CANCEL_REMOVE = range(2)

def extract_drive_id(url_or_id):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    return url_or_id

#Utility function to retrieve all cameras, grouped by brand
def get_all_cameras():
    catalogue_ref = db.collection('catalogue')
    docs = catalogue_ref.stream()

    cameras = {}
    for doc in docs:
        data = doc.to_dict()
        brand = data.get("brand", "Unknown")

        camera = {
            "id": data.get("id"),
            "model": data.get("model"),
            "japanese": data.get("japanese"),
            "battery": data.get("battery"),
            "megapixel": data.get("megapixel"),
            "image1": data.get("image1"),
            "image2": data.get("image2"),
            "video": data.get("video")
        }
        
        if brand not in cameras:
            cameras[brand] = []

        cameras[brand].append(camera)

    return cameras

#Utility function to add new camera to firebase
def add_camera(id, brand, model, japanese, battery, megapixel, image1, image2, video):
    catalogue_ref = db.collection("catalogue")
    data = {
        "id": id,
        "brand": brand,
        "model": model,
        "japanese": japanese,
        "battery": battery,
        "megapixel": megapixel,
        "image1" : image1,
        "image2" : image2,
        "video" : video
    }
    catalogue_ref.add(data)

def camera_id_exists(cam_id: int) -> bool:
    result = db.collection('catalogue').where("id", "==", cam_id).stream()
    return any(result)

#/manageCatalogue command
async def handlerManageCatalogue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = "Manage Catalogue Menu:\n"
                "/viewCatalogue - view existing catalogue\n"
                "/addtoCatalogue - Add new camera to catalogue\n"
    )




#/viewCatalogue command. ASK HARIS ABOUT BUTTON LAYOUT VS LIST
async def handlerViewCatalogue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cameras = get_all_cameras()
    
    if not cameras:
        await update.message.reply_text("No cameras found in catalogue.")
        return
    
    keyboard = []
    for brand in cameras:
        keyboard.append([
            InlineKeyboardButton(brand, callback_data = f"brand_{brand}")
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("📷 Select a camera brand to view models:",
        reply_markup=reply_markup
    )

#Handles clicking a brand in /viewcatalogue
async def handlerViewBrand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    brand = query.data.replace("brand_", "")

    cameras = get_all_cameras()

    if brand not in cameras or not cameras[brand]:
        await query.edit_message_text(f"No cameras found under {brand}.")
        return
    keyboard = [
        [InlineKeyboardButton(
            f"{cam['model']}",
            callback_data=f"camera_{cam['id']}"
        )]
        for cam in cameras[brand]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"📷 Select a {brand} camera to view details:",
        reply_markup=reply_markup
    )

#Handles clicking a camera in /viewcatalogue
async def handlerViewCameraDetails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    camera_id_str = query.data.replace("camera_", "")

    docs = db.collection("catalogue").where("id", "==", int(camera_id_str)).stream()
    cam = next((doc.to_dict() for doc in docs), None)

    if not cam:
        await query.edit_message_text("Camera not found.")
        return

    loading_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="⏳ Loading camera media..."
    )
    media = []
    if "video" in cam:
        media.append(InputMediaVideo(media= cam["video"]))
    if "image1" in cam:
        media.append(InputMediaPhoto(media= cam["image1"]))
    if "image2" in cam:
        media.append(InputMediaPhoto(media= cam["image2"]))
    
    if media:
        await context.bot.send_media_group(chat_id=update.effective_chat.id, media = media)
        await loading_message.delete()

    msg = (
        f"📷 *Camera Details*\n"
        f"• ID: {cam['id']}\n"
        f"• Brand: {cam['brand']}\n"
        f"• Model: {cam['model']}\n"
        f"• Megapixel: {cam['megapixel']}\n"
        f"• Battery: {cam['battery']}\n"
        f"• Japanese Menu: {'Yes' if cam['japanese'] else 'No'}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{cam['id']}"),
            InlineKeyboardButton("🗑 Remove", callback_data=f"remove_{cam['id']}")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

#Handles clicking Remove when viewing camera details
async def handlerRemoveCamera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    cam_id = int(query.data.replace("remove_", ""))
    context.user_data["remove_id"] = cam_id
    
    docs = db.collection("catalogue").where("id", "==", cam_id).stream()
    camera_doc = next((doc.to_dict() for doc in docs), None)
    
    if not camera_doc:
        await query.edit_message_text("❌ Camera not found.")
        return
    
    brand = camera_doc.get("brand", "Unknown")
    model = camera_doc.get("model", "Unknown")

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, delete", callback_data="confirm_remove_yes"),
            InlineKeyboardButton("❌ No, cancel", callback_data="confirm_remove_no")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"⚠️ Are you sure you want to delete *{brand} {model}* (ID: {cam_id})?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

#Handles clicking confirm when Removing Camera
async def handlerConfirmRemove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cam_id = context.user_data.get("remove_id")

    if query.data == "confirm_remove_yes":
        docs = db.collection("catalogue").where("id", "==", cam_id).stream()
        deleted = False
        for doc in docs:
            db.collection("catalogue").document(doc.id).delete()
            deleted = True
        if deleted:
            await query.edit_message_text("✅ Camera successfully deleted.")
        else:
            await query.edit_message_text("❌ Camera not found.")
    else:
        await query.edit_message_text("❌ Deletion Cancelled")

#Handles clicking Edit when viewing camera details
async def handlerEditCamera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cam_id = query.data.replace("edit_", "")
    context.user_data["edit_id"] = int(cam_id)

    keyboard = [
        [InlineKeyboardButton("Brand", callback_data="editfield_brand")],
        [InlineKeyboardButton("Model", callback_data="editfield_model")],
        [InlineKeyboardButton("Megapixel", callback_data="editfield_megapixel")],
        [InlineKeyboardButton("Battery", callback_data="editfield_battery")],
        [InlineKeyboardButton("Japanese Menu", callback_data="editfield_japanese")],
        [InlineKeyboardButton("Video", callback_data="editfield_video")],
        [InlineKeyboardButton("Image 1", callback_data="editfield_image1")],
        [InlineKeyboardButton("Image 2", callback_data="editfield_image2")]
    ]

    await query.edit_message_text(
        "🔧 Which field do you want to edit?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return EDIT_SELECT_FIELD

#Handles which field to edit
async def handlerEditChooseField(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    field = query.data.replace("editfield_","")
    context.user_data["edit_field"] = field
    cam_id = context.user_data["edit_id"]

    docs = db.collection("catalogue").where("id", "==", cam_id).stream()
    camera_doc = next((doc.to_dict() for doc in docs), None)

    if not camera_doc:
        await query.edit_message_text("❌ Camera not found.")
        return ConversationHandler.END

    old_value = camera_doc.get(field, "N/A")

    if field in ["video", "image1", "image2"]:
        await query.edit_message_text(f"Editing {field}, Please enter the sharing URL of the new {field}:")
    else:
        await query.edit_message_text(f"Old value for *{field}* is {old_value}. \nPlease enter the new value for *{field}*:", 
                                    parse_mode = "Markdown")
    return EDIT_INPUT_VALUE

#Handles saving new value
async def handlerEditSave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cam_id = context.user_data["edit_id"]
    field = context.user_data["edit_field"]
    new_value = update.message.text.strip()

    if field == 'japanese':
        if new_value.lower() in ["yes", "y"]:
            new_value = True
        elif new_value.lower() in ["no", "n"]:
            new_value = False
        else:
            await update.message.reply_text("Please enter 'yes' or 'no'. ")
            return EDIT_INPUT_VALUE
    if field in ["video", "image1", "image2"]:
        drive_id = extract_drive_id(new_value)
        new_value = f"https://drive.google.com/uc?export=download&id={drive_id}"
        
    docs = db.collection("catalogue").where("id", "==", cam_id).stream()
    for doc in docs:
        db.collection("catalogue").document(doc.id).update({field: new_value})

    await update.message.reply_text("✅ Camera successfully updated!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

#Handles cancelling edit camera
async def handlerEditCancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌  Edit cancelled.", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END

#Handles Adding new camera to catalogue
async def handlerAddToCatalogueStart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the camera ID (integer):")
    return ADD_ID
#
async def handlerAddToCatalogueID(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        input_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid Integer for ID.")
        return ADD_ID
    
    if camera_id_exists(input_id):
        await update.message.reply_text(f"Camera with ID {input_id} already exists. Please enter a different ID")
        return ADD_ID
    
    context.user_data['id'] = input_id
    await update.message.reply_text("Enter the camera brand:")
    return ADD_BRAND
#
async def handlerAddToCatalogueBrand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand'] = update.message.text
    await update.message.reply_text("Enter the camera model:")
    return ADD_MODEL
#
async def handlerAddToCatalogueModel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['model'] = update.message.text
    await update.message.reply_text("Is the menu for the camera in Japanese? (yes/no)")
    return ADD_JAPANESE
#
async def handlerAddToCatalogueJapanese(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.text.lower()
    if reply in ["yes" , 'y']:
        context.user_data['japanese'] = True
    elif reply in ["no" , 'n']:
        context.user_data['japanese'] = False
    else:
        await update.message.reply_text("Please type 'yes' or 'no'. ")
        return ADD_JAPANESE
    await update.message.reply_text("Enter the battery type: ")
    return ADD_BATTERY
#
async def handlerAddToCatalogueBattery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['battery'] = update.message.text
    await update.message.reply_text("Enter the megapixel count: ")
    return ADD_MEGAPIXEL
#
async def handlerAddToCatalogueMegapixel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['megapixel'] = update.message.text
    await update.message.reply_text("Enter the sharing URL of Image 1:")
    return ADD_IMAGE1
#
async def handlerAddToCatalogueImage1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drive_id = extract_drive_id(update.message.text)
    context.user_data['image1'] = f"https://drive.google.com/uc?export=download&id={drive_id}"
    await update.message.reply_text("Enter the sharing URL of Image 2:")
    return ADD_IMAGE2
#
async def handlerAddToCatalogueImage2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drive_id = extract_drive_id(update.message.text)
    context.user_data['image2'] = f"https://drive.google.com/uc?export=download&id={drive_id}"
    await update.message.reply_text("Enter the sharing URL of Video:")
    return ADD_VIDEO
#
async def handlerAddToCatalogueVideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drive_id = extract_drive_id(update.message.text)
    context.user_data['video'] = f"https://drive.google.com/uc?export=download&id={drive_id}"

    add_camera(
        context.user_data['id'],
        context.user_data['brand'],
        context.user_data['model'],
        context.user_data['japanese'],
        context.user_data['battery'],
        context.user_data['megapixel'],
        context.user_data['image1'],
        context.user_data['image2'],
        context.user_data['video']
    )

    await update.message.reply_text("✅ Camera successfully added to Catalogue!")

    return ConversationHandler.END

#Handles cancelling adding new camera
async def handlerAddToCatalogueCancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


