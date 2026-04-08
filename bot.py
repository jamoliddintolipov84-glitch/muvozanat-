import logging
import asyncio
import sqlite3
import urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = '8710801366:AAGrsujotucdhiAm1aV0vMhbWStk_WBt_Ik' 
CHANNEL_ID = '@jamoliddin_muvozanat' 
MINI_APP_URL = 'https://google.com' # Bu yerga keyinchalik o'z saytingizni qo'yasiz

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH (DOIMIY) ---
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
    # Userni qo'shish (agar yo'q bo'lsa)
    cursor.execute("INSERT OR IGNORE INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, inviter_id))
    # Agar yangi user bo'lsa va uni kimdir taklif qilgan bo'lsa, taklif qilganga ball berish
    if inviter_id and cursor.rowcount > 0:
        cursor.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (inviter_id,))
    conn.commit()
    conn.close()

# --- YORDAMCHI FUNKSIYA ---
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- ASOSIY KOMANDALAR ---

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()
    
    # Taklif qilgan odam ID sini aniqlash
    inviter_id = None
    if len(args) > 1 and args[1].isdigit():
        inviter_id = int(args[1])
        if inviter_id == user_id: inviter_id = None
    
    # Bazaga yozish
    add_or_update_user(user_id, inviter_id)

    if not await check_sub(user_id):
        welcome_text = (
            f"Assalomu alaykum, {name}! **Muvozanat** olamiga xush kelibsiz. ✨\n\n"
            "Hamma uchun vaqt 24 soat emas... ⏳\n"
            "**Muvozanat** — bu sening vaqtingni o'g'rilardan himoya qiluvchi qalqon. 🛡\n\n"
            "🚀 **Boshlash uchun:** Avval rasmiy kanalimizga obuna bo'ling."
        )
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        builder.row(types.InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_sub"))
        await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await show_status(message)

@dp.message(Command("referral"))
async def referral_cmd(message: types.Message):
    if await check_sub(message.from_user.id):
        await show_status(message)
    else:
        await message.answer("Avval kanalga a'zo bo'ling! ✨")

async def show_status(message: types.Message):
    user_id = message.from_user.id
    count = get_user_data(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    if count < 2:
        # Tezkor ulashish (Hook)
        share_msg = "🚀 Do'stim, men 'Muvozanat' ilovasida marafon boshladim. Birga yutamiz! 🔥 Sen ham qo'shil:"
        share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote(share_msg)}"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔥 Do'stlarni chorlash", url=share_url))
        
        await message.answer(
            f"Siz kanalga a'zosiz! ✅\n\n"
            f"💎 **So'nggi qadam:** Ilovani ochish uchun **2 ta do'stni** taklif qiling.\n"
            f"O'zimiz bilan oqibatni uzmaylik! 🌱\n\n"
            f"📊 **Hozirgi takliflar:** {count}/2\n"
            f"🔗 **Havolangiz:** `{ref_link}`",
            reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Ilovani ochish 🪐", web_app=types.WebAppInfo(url=MINI_APP_URL)))
        await message.answer("Barcha shartlar bajarildi! Muvozanatni kashf eting. ✨", reply_markup=builder.as_markup())

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer("💡 **Yo'riqnoma:**\n\n1. Kanalga obuna bo'ling.\n2. 2 ta do'stni taklif qiling.\n3. Ilovadan foydalaning!", parse_mode="Markdown")

@dp.message(Command("aloqa"))
async def aloqa_cmd(message: types.Message):
    await message.answer("📩 **Bog'lanish:**\n\nTez orada javob olasiz. @admin_username ni yozib qo'ying.", parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def callback_check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await show_status(call.message)
    else:
        await call.answer("Siz hali kanalga a'zo bo'lmadingiz! ❌", show_alert=True)

async def main():
    init_db() # Bazani yaratish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())