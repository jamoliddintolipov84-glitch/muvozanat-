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
MINI_APP_URL = 'https://google.com' 
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

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- KOMANDALAR ---
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

    if not await check_sub(user_id):
        welcome_text = (
            f"👋 **Assalomu alaykum, {name}!**\n\n"
            f"⏳ **Muvozanat** — bu hayotingizni tartibga solish va vaqtdan unumli foydalanishni o'rgatuvchi yordamchingiz.\n\n"
            f"🚀 **Botdan foydalanish uchun:**\n"
            f"Avval rasmiy kanalimizga a'zo bo'lishingiz lozim."
        )
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_sub"))
        await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await show_status(message)

# ALOQA
@dp.message(Command("aloqa"))
async def aloqa_cmd(message: types.Message, state: FSMContext):
    await message.answer("💬 **Adminga xabar yuborish**\n\nSavol, taklif yoki g'oyalaringizni yozib qoldiring. Biz albatta javob beramiz!", parse_mode="Markdown")
    await state.set_state(FeedbackState.waiting_for_msg)

@dp.message(FeedbackState.waiting_for_msg)
async def get_feedback(message: types.Message, state: FSMContext):
    user_info = f"👤 **Kimdan:** {message.from_user.full_name}\n🆔 **ID:** `{message.from_user.id}`\n🔗 **User:** @{message.from_user.username or 'yoq'}"
    await bot.send_message(ADMIN_ID, f"📩 **Yangi xabar keldi!**\n\n{user_info}\n\n📝 **Xabar:**\n{message.text}\n\n—\n*Javob berish uchun xabarga Reply qiling*", parse_mode="Markdown")
    await message.answer("✅ **Xabaringiz yuborildi!**\nTez orada administrator javob qaytaradi. Sabr uchun rahmat! ✨", parse_mode="Markdown")
    await state.clear()

# REPLY JAVOB (ADMIN UCHUN)
@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID))
async def reply_to_user(message: types.Message):
    try:
        original_msg = message.reply_to_message.text
        user_id = int(original_msg.split("ID:** `")[1].split("`")[0])
        await bot.send_message(user_id, f"✉️ **Admindan javob keldi:**\n\n{message.text}\n\n📌 *Yana savollar bo'lsa, /aloqa buyrug'idan foydalaning.*", parse_mode="Markdown")
        await message.answer("✅ Javob foydalanuvchiga muvaffaqiyatli yetkazildi!")
    except:
        await message.answer("❌ **Xatolik:** Foydalanuvchi ID raqamini aniqlashda muammo yuz berdi.")

# STATISTIKA
@dp.message(Command("statistika"))
async def stat_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect("muvozanat.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        conn.close()
        
        stat_text = (
            f"📊 **Botning hozirgi holati:**\n\n"
            f"👥 Jami foydalanuvchilar: **{total} ta**\n"
            f"🕒 Yangilangan vaqt: {message.date.strftime('%H:%M:%S')}"
        )
        await message.answer(stat_text, parse_mode="Markdown")

async def show_status(message: types.Message):
    user_id = message.from_user.id
    count = get_user_data(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    if count < 2:
        share_msg = f"🚀 Men 'Muvozanat' ilovasida o'z natijamni yaxshilayapman! Sen ham bizga qo'shil va o'zgarishni boshla: {ref_link}"
        share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote(share_msg)}"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📢 Do'stlarni taklif qilish", url=share_url))
        
        status_text = (
            f"✅ **Tabriklaymiz, siz kanalga a'zosiz!**\n\n"
            f"🎁 **Ilovani ochish uchun:**\n"
            f"Yana **{2 - count} ta** do'stingizni taklif qilishingiz kerak.\n\n"
            f"📊 **Sizning natijangiz:** {count} / 2\n"
            f"🔗 **Taklif havolasi:**\n`{ref_link}`\n\n"
            f"🌱 *O'zimiz bilan oqibatni uzmaylik!*"
        )
        await message.answer(status_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🪐 Ilovani ochish", web_app=types.WebAppInfo(url=MINI_APP_URL)))
        
        win_text = (
            f"🎉 **Barcha shartlar bajarildi!**\n\n"
            f"Siz endi **Muvozanat** olamiga to'liq kirish huquqiga egasiz.\n"
            f"Pastdagi tugmani bosing va kashf etishni boshlang! 👇"
        )
        await message.answer(win_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def callback_check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await show_status(call.message)
    else:
        await call.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
