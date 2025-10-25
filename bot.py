
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates
from random import randint, choices
import string
from datetime import datetime, timedelta
import pytz
import asyncio
import json
import os
import re
from difflib import SequenceMatcher
from keep_alive import keep_alive
keep_alive()


EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{6,}$")

bot = Bot(token='7559245249:AAFKrlVTve_yyvyWpqW9ivCDp6wdmbFXbwI')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

ADMIN_CHAT_ID = 5065566008
user_keys = {}
active_users = {}
user_cooldowns = {}
user_generating = {}

USERS_DIR = "users"
KEYS_FILE = "keys.json"
ULP_DIR = "ulp"
ULP_FILE = os.path.join(ULP_DIR, "ulp.txt")

if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)

if not os.path.exists(ULP_DIR):
    os.makedirs(ULP_DIR)

PH_TZ = pytz.timezone('Asia/Manila')

class KeyState(StatesGroup):
    waiting_for_key = State()

def is_user_active(user_id):
    if user_id not in active_users:
        return False
    
    current_time = get_ph_time()
    expiry_time = active_users[user_id]['expiry']
    
    if expiry_time.year > 3000:
        return True
    
    return expiry_time > current_time

async def check_cooldown(user_id):
    if user_id in user_cooldowns:
        remaining = (user_cooldowns[user_id] - datetime.now()).total_seconds()
        if remaining > 0:
            return int(remaining)
    return 0

async def set_cooldown(user_id):
    user_cooldowns[user_id] = datetime.now() + timedelta(seconds=45)

async def countdown_message(chat_id, seconds):
    countdown_msg = await bot.send_message(chat_id, f"⏳ 𝙲𝚘𝚘𝚕𝚍𝚘𝚠𝚗: {seconds} 𝚜𝚎𝚌𝚘𝚗𝚍𝚜")
    asyncio.create_task(delete_telegram_message_after_delay(chat_id, countdown_msg.message_id, 5))
    
    for i in range(seconds - 1, 0, -1):
        await asyncio.sleep(1)
        try:
            await countdown_msg.edit_text(f"⏳ 𝙲𝚘𝚘𝚕𝚍𝚘𝚠𝚗: {i} 𝚜𝚎𝚌𝚘𝚗𝚍𝚜")
        except:
            pass
    
    await asyncio.sleep(1)
    try:
        await countdown_msg.delete()
    except:
        pass

async def delete_telegram_message_after_delay(chat_id, message_id, delay_seconds=300):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id, message_id)
        print(f"Deleted Telegram message: {message_id}")
    except Exception as e:
        print(f"Error deleting Telegram message {message_id}: {e}")


async def extract_and_send_ulp(chat_id, service_name): 
    try:
        if user_generating.get(chat_id, False):
            return

        cooldown_remaining = await check_cooldown(chat_id)
        if cooldown_remaining > 0:
            asyncio.create_task(countdown_message(chat_id, cooldown_remaining))
            return

        user_generating[chat_id] = True

        if not os.path.exists(ULP_FILE):
            await bot.send_message(chat_id, "❌ 𝚄𝙻𝙿 𝚏𝚒𝚕𝚎 𝚗𝚘𝚝 𝚏𝚘𝚞𝚗𝚍!")
            user_generating[chat_id] = False
            return

        import random
        with open(ULP_FILE, 'r', encoding='utf-8', errors='ignore') as file:
            lines = [line.strip() for line in file if line.strip()]

        random.shuffle(lines)

        formatted_lines = []
        seen_accounts = set()
        seen_passwords = set()
        extracted_indices = set()

        for i, line in enumerate(lines):
            if not line:
                continue

            if '|' in line:
                parts = line.rsplit('|', 2)
            else:
                parts = line.rsplit(':', 2)

            if len(parts) < 2:
                continue

            if len(parts) == 2:
                account_part, password = parts[0].strip(), parts[1].strip()
            else:
                _, account_part, password = parts[-3].strip(), parts[-2].strip(), parts[-1].strip()

            acc_lower = account_part.lower()
            pwd_lower = password.lower()

            if not (EMAIL_PATTERN.match(account_part) or USERNAME_PATTERN.match(account_part)):
                continue

            if acc_lower in seen_accounts or pwd_lower in seen_passwords:
                continue

            seen_accounts.add(acc_lower)
            seen_passwords.add(pwd_lower)
            formatted_lines.append(f"{account_part}:{password}\n")
            extracted_indices.add(i)

            if len(formatted_lines) >= 500:
                break

        new_remaining_lines = [line for i, line in enumerate(lines) if i not in extracted_indices]

        output_filename = f"{service_name}.txt"

        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.writelines(formatted_lines)

        with open(ULP_FILE, 'w', encoding='utf-8') as file:
            file.writelines(line + "\n" for line in new_remaining_lines)

        with open(output_filename, 'rb') as file:
            sent_message = await bot.send_document(
                chat_id,
                file,
                caption=f"""
{service_name} 𝟻𝟶𝟶 𝚄𝚗𝚒𝚚𝚞𝚎 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝚜

👾𝙶𝚎𝚗𝚎𝚛𝚊𝚝𝚎𝚍 𝙳𝚘𝚗𝚎
👾𝙳𝚎𝚕𝚎𝚝𝚒𝚗𝚐 𝚒𝚗 𝟻 𝚖𝚒𝚗𝚞𝚝𝚎𝚜"""
            )

        asyncio.create_task(delete_telegram_message_after_delay(chat_id, sent_message.message_id, 300))
        await set_cooldown(chat_id)
        asyncio.create_task(delete_file_after_delay(output_filename, 300))
        asyncio.create_task(countdown_message(chat_id, 45))
        user_generating[chat_id] = False

    except Exception as e:
        await bot.send_message(chat_id, f"❌ 𝙴𝚛𝚛𝚘𝚛 𝚍𝚞𝚛𝚒𝚗𝚐 𝚎𝚡𝚝𝚛𝚊𝚌𝚝𝚒𝚘𝚗: {str(e)}")
        user_generating[chat_id] = False



async def delete_file_after_delay(filename, delay_seconds=300):
    await asyncio.sleep(delay_seconds)
    try:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Deleted file: {filename}")
    except Exception as e:
        print(f"Error deleting file {filename}: {e}")

def get_user_keyboard(user_id):
    if is_user_active(user_id):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("🌙𝙼𝚘𝚘𝚗", "⚡𝙶𝚊𝚜𝚕𝚒𝚝𝚎")
        keyboard.row("🔐𝙰𝚞𝚝𝚑𝚐𝚘𝚙𝚑", "💯𝟷𝟶𝟶𝟶𝟾𝟸")
        return keyboard
    else:
        return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("👾𝙴𝚗𝚝𝚎𝚛 𝙺𝚎𝚢")

button1 = InlineKeyboardButton(text="👾𝙴𝚗𝚝𝚎𝚛 𝙺𝚎𝚢", callback_data="enter_key")
keyboard_inline = InlineKeyboardMarkup().add(button1)

admin_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
admin_keyboard.row("🔑𝙶𝚎𝚗𝚎𝚛𝚊𝚝𝚎 𝙺𝚎𝚢𝚜")
admin_keyboard.row("🗝️𝙰𝚕𝚕 𝙺𝚎𝚢𝚜")
admin_keyboard.row("👥𝚄𝚜𝚎𝚛 𝙻𝚒𝚜𝚝")
admin_keyboard.row("🗓️𝙳𝚊𝚢𝚜 𝙻𝚎𝚏𝚝")

def generate_key():
    random_letters = ''.join(choices(string.ascii_letters + string.digits, k=4))
    return f"Oni-{random_letters}"

def get_ph_time():
    return datetime.now(PH_TZ)

def format_expiry_time(expiry_datetime):
    if expiry_datetime.year > 3000:
        return "Never expires"
    return expiry_datetime.strftime("%Y-%m-%d %I:%M %p")

def save_keys():
    try:
        with open(KEYS_FILE, 'w') as f:
            json.dump(user_keys, f, indent=2)
    except Exception as e:
        print(f"Error saving keys: {e}")

def load_keys():
    global user_keys
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, 'r') as f:
                user_keys = json.load(f)
                print(f"Loaded {len(user_keys)} keys from file")
        else:
            user_keys = {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        user_keys = {}

def save_user_data(user_id, username, expiry_time, key_used):
    try:
        user_file = os.path.join(USERS_DIR, f"{username}.json")
        user_data = {
            'user_id': user_id,
            'username': username,
            'expiry': expiry_time.isoformat(),
            'key_used': key_used,
            'created_at': get_ph_time().isoformat()
        }
        
        with open(user_file, 'w') as f:
            json.dump(user_data, f, indent=2)
        
        print(f"Saved user data for {username}")
        
    except Exception as e:
        print(f"Error saving user data for {username}: {e}")

def load_all_users():
    global active_users
    active_users = {}
    
    try:
        if not os.path.exists(USERS_DIR):
            return
            
        current_time = get_ph_time()
        loaded_count = 0
        expired_count = 0
        
        for filename in os.listdir(USERS_DIR):
            if filename.endswith('.json'):
                try:
                    user_file = os.path.join(USERS_DIR, filename)
                    with open(user_file, 'r') as f:
                        user_data = json.load(f)
                    
                    expiry_time = datetime.fromisoformat(user_data['expiry'])
                    
                    active_users[user_data['user_id']] = {
                        'username': user_data['username'],
                        'expiry': expiry_time,
                        'key_used': user_data['key_used']
                    }
                    loaded_count += 1
                        
                except Exception as e:
                    print(f"Error loading user file {filename}: {e}")
        
        print(f"Loaded {loaded_count} users")
        
    except Exception as e:
        print(f"Error loading users: {e}")

def remove_user_file(username):
    try:
        user_file = os.path.join(USERS_DIR, f"{username}.json")
        if os.path.exists(user_file):
            os.remove(user_file)
            print(f"Removed user file for {username}")
    except Exception as e:
        print(f"Error removing user file for {username}: {e}")

async def delete_message_after_delay(chat_id, message_id, delay_seconds=8):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

@dp.message_handler(commands=['start', 'help'])
async def welcome(message: types.Message):
    if message.from_user.id == ADMIN_CHAT_ID:
        await message.reply("👑 𝙰𝚍𝚖𝚒𝚗 𝙿𝚊𝚗𝚎𝚕", reply_markup=admin_keyboard)
    else:
        user_id = message.from_user.id
        welcome_text = """➪ 𝙿𝚛𝚒𝚟𝚊𝚝𝚎 𝚄𝙻𝙿 
➪ 𝙵𝚛𝚎𝚜𝚑 𝚄𝙻𝙿 
➪ 𝙰𝚞𝚝𝚘 𝚄𝚙𝚍𝚊𝚝𝚎 
➪ 𝙵𝚊𝚜𝚝 𝙶𝚎𝚗𝚎𝚛𝚊𝚝𝚒𝚘𝚗 
➪ 𝙸𝚗𝚜𝚝𝚊𝚗𝚝 𝙳𝚎𝚕𝚒𝚟𝚎𝚛𝚢 
➪ 𝙰𝚗𝚝𝚒-𝙳𝚞𝚙𝚕𝚒𝚌𝚊𝚝𝚎 𝙵𝚒𝚕𝚝𝚎𝚛 
➪ 𝙿𝚛𝚘𝚝𝚎𝚌𝚝𝚎𝚍 𝚄𝙻𝙿𝚜 
➪︎︎𝚄𝚗𝚕𝚒𝚖𝚒𝚝𝚎𝚍 𝙶𝚎𝚗
➪︎︎𝙰𝚕𝚠𝚊𝚢𝚜 𝚄𝚙 𝚃𝚘 𝙳𝚊𝚝𝚎 
➪︎︎𝙾𝚗𝚕𝚒𝚗𝚎 𝟸𝟺/𝟽 

✰ 𝙾𝚠𝚗𝚎𝚛: 𝙾𝙽𝙸𝙲𝙷𝙰𝙽𝙽𝙴𝙻𝟹𝟶
✰ 𝙿𝚘𝚠𝚎𝚛𝚎𝚍 𝙱𝚢: [𝙳𝙴𝚅] 𝚂𝙰𝙸𝙺𝙸"""

        user_keyboard = get_user_keyboard(user_id)
        
        await message.reply_animation(
            animation="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGY3aDcwaWk5bDcwZnFrNzB2OGdoN2JjbGlsbGZvdWMxd2R2Mjc3OSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/FWtVYDHIxgGgE/giphy.gif",
            caption=welcome_text,
            parse_mode='Markdown',
            reply_markup=user_keyboard
        )

@dp.callback_query_handler(text="enter_key")
async def enter_key_callback(call: types.CallbackQuery, state: FSMContext):
    sent_message = await call.message.answer("👾𝙿𝚕𝚊𝚌𝚎 𝙺𝚎𝚢:")
    asyncio.create_task(delete_message_after_delay(call.message.chat.id, sent_message.message_id))
    await KeyState.waiting_for_key.set()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('gen_'))
async def generate_single_key(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_CHAT_ID:
        await call.answer("❌ 𝙰𝚌𝚌𝚎𝚜𝚜 𝚍𝚎𝚗𝚒𝚎𝚍!")
        return
    
    duration = call.data.split('_')[1]
    key = generate_key()
    
    if duration == "1":
        user_keys[key] = 1
        await call.message.edit_text(f"🔑 𝟷 𝙳𝚊𝚢 𝙺𝚎𝚢: `{key}`", parse_mode='Markdown')
    elif duration == "3":
        user_keys[key] = 3
        await call.message.edit_text(f"🔑 𝟹 𝙳𝚊𝚢𝚜 𝙺𝚎𝚢: `{key}`", parse_mode='Markdown')
    elif duration == "7":
        user_keys[key] = 7
        await call.message.edit_text(f"🔑 𝟽 𝙳𝚊𝚢𝚜 𝙺𝚎𝚢: `{key}`", parse_mode='Markdown')
    elif duration == "15":
        user_keys[key] = 15
        await call.message.edit_text(f"🔑 𝟷𝟻 𝙳𝚊𝚢𝚜 𝙺𝚎𝚢: `{key}`", parse_mode='Markdown')
    elif duration == "30":
        user_keys[key] = 30
        await call.message.edit_text(f"🔑 𝟹𝟶 𝙳𝚊𝚢𝚜 𝙺𝚎𝚢: `{key}`", parse_mode='Markdown')
    elif duration == "lifetime":
        user_keys[key] = 999999
        await call.message.edit_text(f"🔑 𝙻𝚒𝚏𝚎𝚝𝚒𝚖𝚎 𝙺𝚎𝚢: `{key}`", parse_mode='Markdown')
    
    save_keys()
    await call.answer()

@dp.message_handler(state=KeyState.waiting_for_key)
async def process_key(message: types.Message, state: FSMContext):
    key = message.text.strip()
    user_message_id = message.message_id
    username = message.from_user.username or message.from_user.first_name or f"user_{message.from_user.id}"
    
    asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
    
    if key in user_keys:
        days = user_keys[key]
        current_time = get_ph_time()
        
        if days == 999999:
            expiry_time = datetime(9999, 12, 31, tzinfo=PH_TZ)
            sent_message = await message.reply("✅ 𝙻𝚒𝚏𝚎𝚝𝚒𝚖𝚎 𝚊𝚌𝚌𝚎𝚜𝚜 𝚐𝚛𝚊𝚗𝚝𝚎𝚍!")
        else:
            expiry_time = current_time + timedelta(days=days)
            sent_message = await message.reply("✅ 𝙰𝚌𝚌𝚎𝚜𝚜 𝚐𝚛𝚊𝚗𝚝𝚎𝚍!")
        
        asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
        
        save_user_data(message.from_user.id, username, expiry_time, key)
        
        active_users[message.from_user.id] = {
            'username': username,
            'expiry': expiry_time,
            'key_used': key
        }
        
        del user_keys[key]
        save_keys()
        
        user_keyboard = get_user_keyboard(message.from_user.id)
        welcome_message = await message.reply("🎉 𝚆𝚎𝚕𝚌𝚘𝚖𝚎 𝚝𝚘 𝚝𝚑𝚎 𝚜𝚎𝚛𝚟𝚒𝚌𝚎!", reply_markup=user_keyboard)
        
    else:
        sent_message = await message.reply("❌ 𝙸𝚗𝚟𝚊𝚕𝚒𝚍 𝚔𝚎𝚢!")
        asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
    
    await state.finish()

@dp.message_handler(text='👾𝙴𝚗𝚝𝚎𝚛 𝙺𝚎𝚢')
async def enter_key_text(message: types.Message):
    user_message_id = message.message_id
    sent_message = await message.reply("👾𝙿𝚕𝚊𝚌𝚎 𝙺𝚎𝚢:")
    
    asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
    asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
    
    await KeyState.waiting_for_key.set()

@dp.message_handler(text='🌙𝙼𝚘𝚘𝚗')
async def moon_handler(message: types.Message):
    user_id = message.from_user.id
    user_message_id = message.message_id
    
    asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
    
    if not is_user_active(user_id):
        user_keyboard = get_user_keyboard(user_id)
        sent_message = await message.reply("❌ 𝚈𝚘𝚞𝚛 𝚊𝚌𝚌𝚎𝚜𝚜 𝚑𝚊𝚜 𝚎𝚡𝚙𝚒𝚛𝚎𝚍. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛 𝚊 𝚗𝚎𝚠 𝚔𝚎𝚢.", reply_markup=user_keyboard)
        asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
        return
    
    cooldown_remaining = await check_cooldown(user_id)
    if cooldown_remaining > 0:
        asyncio.create_task(countdown_message(message.chat.id, cooldown_remaining))
        return
    
    if user_generating.get(user_id, False):
        return
    
    sent_message = await message.reply("🌙 𝙼𝚘𝚘𝚗 𝚜𝚎𝚛𝚟𝚒𝚌𝚎 𝚒𝚜 𝚗𝚘𝚠 𝚛𝚞𝚗𝚗𝚒𝚗𝚐...")
    asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
    
    await extract_and_send_ulp(message.chat.id, "Moon")

@dp.message_handler(text='⚡𝙶𝚊𝚜𝚕𝚒𝚝𝚎')
async def gaslite_handler(message: types.Message):
    user_id = message.from_user.id
    user_message_id = message.message_id
    
    asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
    
    if not is_user_active(user_id):
        user_keyboard = get_user_keyboard(user_id)
        sent_message = await message.reply("❌ 𝚈𝚘𝚞𝚛 𝚊𝚌𝚌𝚎𝚜𝚜 𝚑𝚊𝚜 𝚎𝚡𝚙𝚒𝚛𝚎𝚍. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛 𝚊 𝚗𝚎𝚠 𝚔𝚎𝚢.", reply_markup=user_keyboard)
        asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
        return
    
    cooldown_remaining = await check_cooldown(user_id)
    if cooldown_remaining > 0:
        asyncio.create_task(countdown_message(message.chat.id, cooldown_remaining))
        return
    
    if user_generating.get(user_id, False):
        return
    
    sent_message = await message.reply("⚡ 𝙶𝚊𝚜𝚕𝚒𝚝𝚎 𝚜𝚎𝚛𝚟𝚒𝚌𝚎 𝚒𝚜 𝚗𝚘𝚠 𝚛𝚞𝚗𝚗𝚒𝚗𝚐...")
    asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
    
    await extract_and_send_ulp(message.chat.id, "Gaslite")

@dp.message_handler(text='🔐𝙰𝚞𝚝𝚑𝚐𝚘𝚙𝚑')
async def authgoph_handler(message: types.Message):
    user_id = message.from_user.id
    user_message_id = message.message_id
    
    asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
    
    if not is_user_active(user_id):
        user_keyboard = get_user_keyboard(user_id)
        sent_message = await message.reply("❌ 𝚈𝚘𝚞𝚛 𝚊𝚌𝚌𝚎𝚜𝚜 𝚑𝚊𝚜 𝚎𝚡𝚙𝚒𝚛𝚎𝚍. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛 𝚊 𝚗𝚎𝚠 𝚔𝚎𝚢.", reply_markup=user_keyboard)
        asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
        return
    
    cooldown_remaining = await check_cooldown(user_id)
    if cooldown_remaining > 0:
        asyncio.create_task(countdown_message(message.chat.id, cooldown_remaining))
        return
    
    if user_generating.get(user_id, False):
        return
    
    sent_message = await message.reply("🔐 𝙰𝚞𝚝𝚑𝚐𝚘𝚙𝚑 𝚜𝚎𝚛𝚟𝚒𝚌𝚎 𝚒𝚜 𝚗𝚘𝚠 𝚛𝚞𝚗𝚗𝚒𝚗𝚐...")
    asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
    
    await extract_and_send_ulp(message.chat.id, "Authgoph")

@dp.message_handler(text='💯𝟷𝟶𝟶𝟶𝟾𝟸')
async def number_handler(message: types.Message):
    user_id = message.from_user.id
    user_message_id = message.message_id
    
    asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
    
    if not is_user_active(user_id):
        user_keyboard = get_user_keyboard(user_id)
        sent_message = await message.reply("❌ 𝚈𝚘𝚞𝚛 𝚊𝚌𝚌𝚎𝚜𝚜 𝚑𝚊𝚜 𝚎𝚡𝚙𝚒𝚛𝚎𝚍. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛 𝚊 𝚗𝚎𝚠 𝚔𝚎𝚢.", reply_markup=user_keyboard)
        asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
        return
    
    cooldown_remaining = await check_cooldown(user_id)
    if cooldown_remaining > 0:
        asyncio.create_task(countdown_message(message.chat.id, cooldown_remaining))
        return
    
    if user_generating.get(user_id, False):
        return
    
    sent_message = await message.reply("💯 𝟷𝟶𝟶𝟶𝟾𝟸 𝚜𝚎𝚛𝚟𝚒𝚌𝚎 𝚒𝚜 𝚗𝚘𝚠 𝚛𝚞𝚗𝚗𝚒𝚗𝚐...")
    asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
    
    await extract_and_send_ulp(message.chat.id, "100082")

@dp.message_handler()
async def kb_answer(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    
    if user_id == ADMIN_CHAT_ID:
        if text == '🔑𝙶𝚎𝚗𝚎𝚛𝚊𝚝𝚎 𝙺𝚎𝚢𝚜':
            key_generation_keyboard = InlineKeyboardMarkup(row_width=2)
            key_generation_keyboard.add(
                InlineKeyboardButton("𝟷 𝙳𝚊𝚢", callback_data="gen_1"),
                InlineKeyboardButton("𝟹 𝙳𝚊𝚢𝚜", callback_data="gen_3"),
                InlineKeyboardButton("𝟽 𝙳𝚊𝚢𝚜", callback_data="gen_7"),
                InlineKeyboardButton("𝟷𝟻 𝙳𝚊𝚢𝚜", callback_data="gen_15"),
                InlineKeyboardButton("𝟹𝟶 𝙳𝚊𝚢𝚜", callback_data="gen_30"),
                InlineKeyboardButton("𝙻𝚒𝚏𝚎𝚝𝚒𝚖𝚎", callback_data="gen_lifetime")
            )
            await message.reply("🔑 𝙲𝚑𝚘𝚘𝚜𝚎 𝚔𝚎𝚢 𝚍𝚞𝚛𝚊𝚝𝚒𝚘𝚗:", reply_markup=key_generation_keyboard)
            
        elif text == '🗝️𝙰𝚕𝚕 𝙺𝚎𝚢𝚜':
            if not user_keys:
                await message.reply("📋 𝙽𝚘 𝚞𝚗𝚞𝚜𝚎𝚍 𝚔𝚎𝚢𝚜 𝚊𝚟𝚊𝚒𝚕𝚊𝚋𝚕𝚎.")
            else:
                keys_text = "🗝️ 𝙰𝚟𝚊𝚒𝚕𝚊𝚋𝚕𝚎 𝙺𝚎𝚢𝚜:"
                for key, days in user_keys.items():
                    if days == 999999:
                        keys_text += f"🔑 `{key}` - 𝙻𝚒𝚏𝚎𝚝𝚒𝚖𝚎"
                    else:
                        keys_text += f"🔑 `{key}` - {days} 𝚍𝚊𝚢𝚜"
                await message.reply(keys_text, parse_mode='Markdown')
                
        elif text == '👥𝚄𝚜𝚎𝚛 𝙻𝚒𝚜𝚝':
            current_time = get_ph_time()
            active_user_list = {}
            
            for user_id_check, data in active_users.items():
                expiry = data['expiry']
                if expiry.year > 3000 or expiry > current_time:
                    active_user_list[user_id_check] = data
            
            if not active_user_list:
                await message.reply("📋 𝙽𝚘 𝚊𝚌𝚝𝚒𝚟𝚎 𝚞𝚜𝚎𝚛𝚜.")
            else:
                users_text = "👥 𝙰𝚌𝚝𝚒𝚟𝚎 𝚄𝚜𝚎𝚛𝚜:"
                
                remove_keyboard = InlineKeyboardMarkup()
                
                for user_id_check, data in active_user_list.items():
                    username = data['username']
                    expiry = data['expiry']
                    
                    if expiry.year > 3000:
                        status = "𝙻𝚒𝚏𝚎𝚝𝚒𝚖𝚎"
                    else:
                        if expiry > current_time:
                            time_diff = expiry - current_time
                            days_left = time_diff.days
                            hours_left = time_diff.seconds // 3600
                            
                            if days_left > 0:
                                status = f"{days_left} 𝚍𝚊𝚢𝚜 𝚕𝚎𝚏𝚝"
                            elif hours_left > 0:
                                status = f"{hours_left} 𝚑𝚘𝚞𝚛𝚜 𝚕𝚎𝚏𝚝"
                            else:
                                status = "𝙻𝚎𝚜𝚜 𝚝𝚑𝚊𝚗 1 𝚑𝚘𝚞𝚛 𝚕𝚎𝚏𝚝"
                        else:
                            status = "𝙴𝚡𝚙𝚒𝚛𝚎𝚍"
                    
                    users_text += f"""
👤 @{username} (ID: {user_id_check})
📅 {status}

🔑 𝙺𝚎𝚢: `{data['key_used']}`
⏰ 𝙴𝚡𝚙𝚒𝚛𝚎𝚜: {format_expiry_time(expiry)}
"""
                    
                    remove_keyboard.add(InlineKeyboardButton(f"🗑️ Remove @{username}", callback_data=f"remove_{user_id_check}"))
                
                await message.reply(users_text, parse_mode='Markdown', reply_markup=remove_keyboard)
                
        elif text == '🗓️𝙳𝚊𝚢𝚜 𝙻𝚎𝚏𝚝':
            current_time = get_ph_time()
            days_left_text = "🗓️ 𝙳𝚊𝚢𝚜 𝙻𝚎𝚏𝚝 𝚏𝚘𝚛 𝙰𝚕𝚕 𝚄𝚜𝚎𝚛𝚜:"
            
            for user_id_check, data in active_users.items():
                username = data['username']
                expiry = data['expiry']
                
                if expiry.year > 3000:
                    days_left_text += f"👤 @{username}: 𝙻𝚒𝚏𝚎𝚝𝚒𝚖𝚎"
                else:
                    if expiry > current_time:
                        time_diff = expiry - current_time
                        days_left = time_diff.days
                        hours_left = time_diff.seconds // 3600
                        
                        if days_left > 0:
                            days_left_text += f"👤 @{username}: {days_left} 𝚍𝚊𝚢𝚜 𝚕𝚎𝚏𝚝"
                        elif hours_left > 0:
                            days_left_text += f"👤 @{username}: {hours_left} 𝚑𝚘𝚞𝚛𝚜 𝚕𝚎𝚏𝚝"
                        else:
                            days_left_text += f"👤 @{username}: 𝙻𝚎𝚜𝚜 𝚝𝚑𝚊𝚗 1 𝚑𝚘𝚞𝚛 𝚕𝚎𝚏𝚝"
                    else:
                        days_left_text += f"👤 @{username}: 𝙴𝚡𝚙𝚒𝚛𝚎𝚍"
            
            await message.reply(days_left_text)
    else:
        user_message_id = message.message_id
        if not is_user_active(user_id):
            user_keyboard = get_user_keyboard(user_id)
            sent_message = await message.reply("❌ 𝚈𝚘𝚞𝚛 𝚊𝚌𝚌𝚎𝚜𝚜 𝚑𝚊𝚜 𝚎𝚡𝚙𝚒𝚛𝚎𝚍. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚎𝚗𝚝𝚎𝚛 𝚊 𝚗𝚎𝚠 𝚔𝚎𝚢.", reply_markup=user_keyboard)
            asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
            asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))
        else:
            sent_message = await message.reply("❓ 𝙸𝚗𝚟𝚊𝚕𝚒𝚍 𝚘𝚙𝚝𝚒𝚘𝚗. 𝙿𝚕𝚎𝚊𝚜𝚎 𝚞𝚜𝚎 𝚝𝚑𝚎 𝚔𝚎𝚢𝚋𝚘𝚊𝚛𝚍 𝚘𝚛 𝚌𝚘𝚗𝚝𝚊𝚌𝚝 𝙰𝙳𝙼𝙸𝙽.")
            asyncio.create_task(delete_message_after_delay(message.chat.id, user_message_id))
            asyncio.create_task(delete_message_after_delay(message.chat.id, sent_message.message_id))

@dp.callback_query_handler(lambda c: c.data.startswith('remove_'))
async def remove_user_callback(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_CHAT_ID:
        await call.answer("❌ 𝙰𝚌𝚌𝚎𝚜𝚜 𝚍𝚎𝚗𝚒𝚎𝚍!")
        return
    
    user_id_to_remove = int(call.data.split('_')[1])
    
    if user_id_to_remove in active_users:
        username = active_users[user_id_to_remove]['username']
        del active_users[user_id_to_remove]
        remove_user_file(username)
        await call.message.edit_text(f"✅ 𝚄𝚜𝚎𝚛 @{username} 𝚛𝚎𝚖𝚘𝚟𝚎𝚍 𝚜𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢!")
    else:
        await call.message.edit_text("❌ 𝚄𝚜𝚎𝚛 𝚗𝚘𝚝 𝚏𝚘𝚞𝚗𝚍!")
    
    await call.answer()

async def periodic_cleanup():
    while True:
        try:
            current_time = get_ph_time()
            expired_users = []
            
            for user_id, data in active_users.items():
                if data['expiry'].year <= 3000 and data['expiry'] <= current_time:
                    expired_users.append((user_id, data['username']))
            
            for user_id, username in expired_users:
                del active_users[user_id]
                remove_user_file(username)
                print(f"Removed expired user: {username}")
            
            if expired_users:
                print(f"Cleaned up {len(expired_users)} expired users")
            
        except Exception as e:
            print(f"Error in cleanup: {e}")
        
        await asyncio.sleep(3600)

async def on_startup(dp):
    load_keys()
    load_all_users()
    asyncio.create_task(periodic_cleanup())
    print("Bot started successfully!")

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except TerminatedByOtherGetUpdates:
        print("Bot was terminated by another instance.")
    except Exception as e:
        print(f"Error starting bot: {e}")