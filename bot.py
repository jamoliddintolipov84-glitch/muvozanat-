import logging
import asyncio
import sqlite3
import urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- SOZLAMALAR ---
API_TOKEN = '8710801366:AAGrsujotucdhiAm1aV0vMhbWStk_WBt_Ik' 
CHANNEL_ID = '@jamoliddin_muvozanat' 
MINI_APP_URL = 'https://muvozanat.lovable.app' 
ADMIN_ID = 5711329638 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class FeedbackState(StatesGroup):
    waiting_for_msg = State()

# --- BAZA ---
def init_db():
    conn = sqlite3.connect("muvozanat.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, ref_count INTEGER DEFAULT 0, invited_by INTEGER)''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect("muvozanat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_or_update_user(user_id, inviter_id=None):
    conn = sqlite3.connect("muvozanat.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, inviter_id))
    if inviter_id and cursor.rowcount > 0:
        cursor.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (inviter_id,))
    conn.commit()
    conn.close()

# --- ASOSIY HANDLERLAR ---

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()
    inviter_id = None
    if len(args) > 1 and args[1].isdigit():
        inviter_id = int(args[1])
        if inviter_id == user_id: inviter_id = None
    
    add_or_update_user(user_id, inviter_id)

    # MAJBURIY EMAS, TAVSIYAVIY START XABARI
    welcome_text = (
        f"🌟 **Xush kelibsiz, {name}!**\n\n"
        f"**Muvozanat** — bu sizning muvaffaqiyat va ichki xotirjamlik sari yo'lingizdir. ⚖️\n\n"
        f"📢 **Manfaatli tavsiya:**\n"
        f"Kunlik motivatsiya va foydali ilmlar uchun rasmiy kanalimizga obuna bo'lishingizni tavsiya qilamiz. Bu sizga rivojlanishda yordam beradi.\n\n"
        f"🔗 **Do'stlar bilan ulashish:**\n"
        f"Atrofingizdagilarga ham manfaat ulashishni xohlasangiz, ularni taklif qiling!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🪐 Ilovani ochish", web_app=types.WebAppInfo(url=MINI_APP_URL)))
    builder.row(types.InlineKeyboardButton(text="📢 Manfaatli kanal", url=f"https://t.me/{CHANNEL_ID[1:]}"))
    builder.row(types.InlineKeyboardButton(text="👥 Do'stlarni taklif qilish", callback_data="show_ref"))
    
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "show_ref")
async def show_ref_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    share_msg = f"🤫 Shoshiling! 'Muvozanat' olamiga kirish eshigi ochildi... Faqat haqiqiy o'zgarishni xohlaganlar uchun: {ref_link}"
    share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote(share_msg)}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Ulashish", url=share_url))
    
    await call.message.answer(
        f"✨ **Manfaat ulashish — eng yaxshi fazilat!**\n\n"
        f"Sizning taklif havolangiz:\n`{ref_link}`\n\n"
        f"Do'stlaringizga ham hayotdagi muvozanatni topishga yordam bering.",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )
    await call.answer()

# --- ALOQA VA STATISTIKA (O'ZGARISHSIZ) ---
@dp.message(Command("aloqa"))
async def aloqa_cmd(message: types.Message, state: FSMContext):
    await message.answer("💬 **Savolingizni yozing:**", parse_mode="Markdown")
    await state.set_state(FeedbackState.waiting_for_msg)

@dp.message(FeedbackState.waiting_for_msg)
async def get_feedback(message: types.Message, state: FSMContext):
    user_info = f"👤 {message.from_user.full_name} | ID: `{message.from_user.id}`"
    await bot.send_message(ADMIN_ID, f"📩 **Xabar:**\n{user_info}\n\n{message.text}", parse_mode="Markdown")
    await message.answer("✅ Yuborildi!", parse_mode="Markdown")
    await state.clear()

@dp.message(Command("statistika"))
async def stat_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect("muvozanat.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        conn.close()
        await message.answer(f"📊 Jami foydalanuvchilar: {total}")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
