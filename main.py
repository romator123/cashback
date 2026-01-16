import asyncio
import logging
import os
import sys
import json

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

import config
import ocr
import db  # Import our database module

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logging.error("Please set your BOT_TOKEN in config.py or environment variables.")
    sys.exit(1)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Ensure temp directory exists for downloads
TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- WEB APP URL ---
WEBAPP_URL = "https://romator123.github.io/cashback/webapp/index.html"

# --- Startup Hook ---
@dp.startup()
async def on_startup(bot: Bot):
    await db.init_db()
    logging.info("Database initialized.")

# --- Commands ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем клавиатуру с кнопкой Web App
    kb = [
        [KeyboardButton(text="📱 Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(
        "👋 **Привет! Я бот для учета кешбэков.**\n\n"
        "🔹 **Как добавить кешбэк:**\n"
        "1. Нажми кнопку **\"📱 Открыть приложение\"** внизу.\n"
        "2. Или отправь скриншот из банка (пока в тесте).\n\n"
        "🔹 **Как искать:**\n"
        "Просто напиши категорию, например: **Такси** или **Еда**.\n\n"
        "🔹 **Мои кешбэки:**\n"
        "/my - Показать весь список\n"
        "/reset - Удалить всё (новый месяц)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command("my"))
async def cmd_my(message: types.Message):
    rows = await db.get_all_cashbacks(message.from_user.id)
    if not rows:
        await message.answer("У тебя пока нет сохраненных кешбэков.")
        return

    text = "📋 **Твои кешбэки:**\n\n"
    current_bank = None
    for bank, category, percent in rows:
        if bank != current_bank:
            text += f"\n🏦 **{bank}**:\n"
            current_bank = bank
        text += f"— {category}: {percent}%\n"

    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    await db.clear_cashbacks(message.from_user.id)
    await message.answer("🗑 Все ваши данные удалены. Можно заводить новые на этот месяц!")

# --- Handlers ---

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    
    bank = data.get('bank')
    category = data.get('category')
    
    # Convert percent to float/int safely
    try:
        percent = float(data.get('percent'))
    except (ValueError, TypeError):
        percent = 0.0
    
    if bank and category:
        await db.add_cashback(message.from_user.id, bank, category, percent)
        
        response_text = (
            f"✅ **Сохранено!**\n"
            f"🏦 {bank} — {category}: {percent}%"
        )
        await message.answer(response_text, parse_mode="Markdown")
    else:
        await message.answer("Ошибка данных.")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    # Get the largest available photo
    photo = message.photo[-1]
    
    file_id = photo.file_id
    file_unique_id = photo.file_unique_id
    
    # Define path to save
    file_path = os.path.join(TEMP_DIR, f"{file_unique_id}.jpg")
    
    await message.reply("Скачиваю и обрабатываю фото... Это может занять несколько секунд.")
    
    try:
        # Download the file
        await bot.download(photo, destination=file_path)
        
        # Process with OCR
        text_lines = ocr.text_from_image(file_path)
        
        # Clean up the file
        os.remove(file_path)
        
        if not text_lines:
            await message.reply("Не удалось распознать текст на изображении.")
            return
            
        # Join text for display (simple version)
        result_text = "\n".join(text_lines)
        
        if len(result_text) > 4000:
             result_text = result_text[:4000] + "..."
             
        await message.reply(f"🔍 **Распознанный текст:**\n(Пока просто показываю, скоро научусь сохранять)\n\n{result_text}")
        
    except Exception as e:
        logging.error(f"Error handling photo: {e}")
        await message.reply("Произошла ошибка при обработке изображения.")

# Handle text search (must be last handler usually)
@dp.message(F.text)
async def handle_text_search(message: types.Message):
    query = message.text.strip()
    
    # Ignore commands
    if query.startswith("/"):
        return

    results = await db.get_best_cashback(message.from_user.id, query)
    
    if not results:
        await message.answer(f"Ничего не нашел по запросу '{query}'. Попробуй добавить через кнопку.")
        return

    text = f"🏆 **Лучший кешбэк для '{query}':**\n\n"
    for bank, category, percent in results:
        text += f"✅ **{percent}%** — {bank} ({category})\n"
        
    await message.answer(text, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())