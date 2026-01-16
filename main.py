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

# --- ВАЖНО: ВСТАВЬ СЮДА URL СВОЕГО WEB APP (HTTPS) ---
# Если тестируешь локально, используй ngrok URL, например: "https://xxxx-xx-xx.ngrok-free.app/webapp/index.html"
# Для GitHub Pages это будет: "https://username.github.io/repo/webapp/index.html"
WEBAPP_URL = "https://roman.github.io/cashback/webapp/index.html" 

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем клавиатуру с кнопкой Web App
    kb = [
        [KeyboardButton(text="📱 Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(
        "Привет! Я бот для учета кешбэков.\n"
        "Ты можешь отправить мне скриншот (OCR) или нажать кнопку ниже, "
        "чтобы добавить кешбэк вручную через Mini App.",
        reply_markup=keyboard
    )

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    
    bank = data.get('bank')
    category = data.get('category')
    percent = data.get('percent')
    
    # Тут можно сохранить в базу данных
    response_text = (
        f"✅ **Кешбэк сохранен!**\n\n"
        f"🏦 Банк: {bank}\n"
        f"🏷 Категория: {category}\n"
        f"📉 Процент: {percent}%"
    )
    
    await message.answer(response_text)

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
        
        # Send back the raw text (for verification)
        # Limit message length just in case
        if len(result_text) > 4000:
             result_text = result_text[:4000] + "..."
             
        await message.reply(f"Распознанный текст:\n\n{result_text}")
        
    except Exception as e:
        logging.error(f"Error handling photo: {e}")
        await message.reply("Произошла ошибка при обработке изображения.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
