# -*- coding: utf-8 -*-
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import uuid

# CONFIG
BOT_TOKEN = "7069586996:AAG5A-LLSWaQrLQ9EqM8_JihaQI3I90bFik"
SELLER_ID = 7241783674
IMAGE_URL = "https://i.ibb.co/GvdwqBgR/IMG-20250409-100556.jpg"

# States
FOOD, TAX, DISTANCE, CONFIRM, ADDRESS, SCREENSHOT = range(6)
user_lang = {}

# Language toggle
def get_text(lang, en, hi, hing):
    if lang == "hi": return hi
    elif lang == "hing": return hing
    else: return en

# Reply buttons
def main_keyboard(lang="en"):
    return ReplyKeyboardMarkup([
        [KeyboardButton("Order"), KeyboardButton("Contact")],
        [KeyboardButton("Language"), KeyboardButton("Menu")],
        [KeyboardButton("Help"), KeyboardButton("Cancel")]
    ], resize_keyboard=True)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang[update.effective_user.id] = "hi"
    await update.message.reply_text("स्वागत है! Order देने के लिए 'Order' दबाएं।", reply_markup=main_keyboard("hi"))

# Language toggle
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    current = user_lang.get(uid, "hi")
    new = "en" if current == "hi" else "hing" if current == "en" else "hi"
    user_lang[uid] = new
    msg = get_text(new, "Language set to English", "भाषा हिंदी में सेट की गई", "Language ab Hinglish me hai")
    await update.message.reply_text(msg, reply_markup=main_keyboard(new))

# Menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "hi")
    msg = get_text(
        lang,
        "Steps:\n1. Enter food amount\n2. Enter tax + platform fee\n3. Enter distance (max 7 km)\n\nThen confirm.",
        "स्टेप्स:\n1. भोजन राशि डालें\n2. टैक्स + प्लेटफॉर्म शुल्क जोड़ें\n3. दूरी दर्ज करें (अधिकतम 7km)\n\nफिर पुष्टि करें।",
        "Steps:\n1. Food amount daalo\n2. Tax + fee jodo\n3. Distance daalo (max 7km)\n\nThen confirm karo."
    )
    await update.message.reply_text(msg)

# Contact
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Seller से बात करने के लिए:\n👉 https://t.me/katiharvloger2")

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Order process cancel कर दिया गया।", reply_markup=main_keyboard())

# Order
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_lang.get(uid, "hi")
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=IMAGE_URL)
    msg = get_text(
        lang,
        "1. Enter food amount\n2. Enter tax + GST + fee\n3. Distance (max 7km)",
        "1. भोजन राशि दर्ज करें\n2. टैक्स + जीएसटी + शुल्क\n3. दूरी (7km तक)",
        "1. Food amount daalo\n2. GST + fee daalo\n3. Distance (7km tak)"
    )
    await update.message.reply_text(msg + "\n\nकृपया ₹ में amount भेजें:", reply_markup=ReplyKeyboardRemove())
    return FOOD

async def get_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        if amount < 199:
            await update.message.reply_text("₹199 से कम का order स्वीकार नहीं है।")
            return FOOD
        context.user_data["food"] = amount
        await update.message.reply_text("अब Tax + GST + Fee टोटल ₹ में भेजें:")
        return TAX
    except:
        await update.message.reply_text("सही ₹ राशि भेजें।")
        return FOOD

async def get_tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tax = int(update.message.text)
        context.user_data["tax"] = tax
        await update.message.reply_text("Delivery दूरी (km) में भेजें (max 7km):")
        return DISTANCE
    except:
        await update.message.reply_text("सही ₹ राशि भेजें।")
        return TAX

async def get_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        distance = float(update.message.text)
        if distance > 7:
            await update.message.reply_text("डिलीवरी सिर्फ 7km तक उपलब्ध है।")
            return DISTANCE
        food = context.user_data["food"]
        tax = context.user_data["tax"]

        if 199 <= food <= 248:
            discount, extra = 90, 15
        elif 249 <= food <= 298:
            discount, extra = 110, 0
        else:
            discount, extra = 125, 0

        total = food + tax + extra - discount
        context.user_data.update({
            "distance": distance,
            "discount": discount,
            "extra": extra,
            "total": total
        })

        await update.message.reply_text(
            f"""Order Summary:
Food: ₹{food}
Tax: ₹{tax}
Distance: {distance} km
Discount: ₹{discount}
Extra: ₹{extra}
Final Amount: ₹{total}

Order confirm karein? (yes/no)"""
        )
        return CONFIRM
    except:
        await update.message.reply_text("Distance km में भेजें।")
        return DISTANCE

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "yes" in update.message.text.lower():
        await update.message.reply_text("अब Swiggy वाला Address Link भेजें:")
        return ADDRESS
    else:
        await update.message.reply_text("Order cancel किया गया।", reply_markup=main_keyboard())
        return ConversationHandler.END

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    await update.message.reply_text("अब Cart का Screenshot भेजें:")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["screenshot"] = update.message.photo[-1].file_id
        order_id = str(uuid.uuid4())[:8].upper()
        context.user_data["order_id"] = order_id
        user = update.effective_user

        # Receipt to user
        await update.message.reply_text(
            f"""✅ Order Confirmed!

🧾 Order ID: {order_id}
Final Amount: ₹{context.user_data['total']}
Thank you! Seller ko details bhej diya gaya hai.""",
            reply_markup=main_keyboard()
        )

        # Message to seller
        msg = (
            f"🛒 New Order!\n"
            f"Order ID: {order_id}\n"
            f"👤 User: @{user.username or 'N/A'}\n"
            f"ID: {user.id}\n\n"
            f"Food: ₹{context.user_data['food']}\n"
            f"Tax: ₹{context.user_data['tax']}\n"
            f"Distance: {context.user_data['distance']} km\n"
            f"Discount: ₹{context.user_data['discount']}\n"
            f"Extra: ₹{context.user_data['extra']}\n"
            f"Total: ₹{context.user_data['total']}\n"
            f"Address: {context.user_data['address']}"
        )
        await context.bot.send_photo(chat_id=SELLER_ID, photo=context.user_data["screenshot"], caption=msg)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Screenshot भेजें।")
        return SCREENSHOT

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Order$"), handle_order)],
        states={
            FOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_food)],
            TAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tax)],
            DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_distance)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Cancel$"), cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("help", contact))  # help opens contact
    app.add_handler(CommandHandler("order", handle_order))

    app.run_polling()

if __name__ == "__main__":
    main()

  
