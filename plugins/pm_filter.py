import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
lock = asyncio.Lock()
from database.users_chats_db import db
from database.refer import referdb
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import *
from fuzzywuzzy import process
from database.users_chats_db import db
from database.ia_filterdb import Media, Media2, get_file_details, get_search_results, get_bad_files
import logging
from urllib.parse import quote_plus
from Lucia.util.file_properties import get_name, get_hash, get_media_file_size
from database.topdb import silentdb
import requests
import string
import tracemalloc

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

tracemalloc.start()

TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    if EMOJI_MODE:
        await message.react(emoji=random.choice(REACTIONS))
    await silentdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        if settings['auto_ffilter']:
            if re.search(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
                if await is_check_admin(client, message.chat.id, message.from_user.id):
                    return
                return await message.delete()   
            await auto_filter(client, message)
    else:
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ✅\n\n📂 ꜰɪʟᴇꜱ ꜰᴏᴜɴᴅ : {str(total_results)}\n🔍 ꜱᴇᴀʀᴄʜ :</b> <code>{search}</code>\n\n<b>‼️ ᴛʜɪs ɪs ᴀ <u>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</u> sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\n📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ : 👇</b>",   
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ᴊᴏɪɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)]]))


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    bot_id = bot.me.id
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if EMOJI_MODE:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    if content.startswith(("/", "#")):
        return  
    try:
        await silentdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        if pm_search:
            await auto_filter(bot, message)
        else:
            await message.reply_text(
             text=f"<b><i>ɪ ᴀᴍ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ 🚫 ᴊᴏɪɴ ᴍʏ ɢʀᴏᴜᴘ ꜰʀᴏᴍ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ᴛʜᴇʀᴇ !</i></b>",   
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ꜱᴇᴀʀᴄʜʜᴇʀᴇ ", url=GRP_LNK)]])
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('ɪɴᴠɪᴛᴇ ɪɪɴᴋ', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='premium')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await bot.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto("https://graph.org/file/1a2e64aee3d4d10edd930.jpg")
        )
    await query.message.edit_text(
        text=f'Hay Your refer link:\n\nhttps://t.me/{bot.me.username}?start=reff_{query.from_user.id}\n\nShare this link with your friends, Each time they join,  you will get 10 refferal points and after 100 points you will get 1 month premium subscription.',
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
        )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        try:
            offset = int(offset)
        except:
            offset = 0
        if BUTTONS.get(key)!=None:
            search = BUTTONS.get(key)
        else:
            search = FRESH.get(key)
        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
        try:
            n_offset = int(n_offset)
        except:
            n_offset = 0
        if not files:
            return
        temp.GETALL[key] = files
        temp.SHORT[query.from_user.id] = query.message.chat.id
        settings = await get_settings(query.message.chat.id)
        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                    ),
                ]
                for file in files
            ]
            btn.insert(0, 
                [ 
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")
           
            ])
        else:
            btn = []
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}") 
           
            ])
        try:
            if settings['max_btn']:
                if 0 < offset <= 10:
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - 10
                if n_offset == 0:
                    btn.append(
                        [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                    )
                elif off_set is None:
                    btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                            InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                            InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                        ],
                    )
            else:
                if 0 < offset <= int(MAX_B_TN):
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - int(MAX_B_TN)
                if n_offset == 0:
                    btn.append(
                        [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                    )
                elif off_set is None:
                    btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                            InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                            InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                        ],
                    )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        if not settings.get('button'):
            cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
            time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
            remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
            cap = await get_cap(settings, remaining_seconds, files, query, total, search, offset)
            try:
                await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            except MessageNotModified:
                pass
        else:
            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        await query.answer()
    except Exception as e:
        print(f"Error In Next Funtion - {e}")

@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    try:
        try:
            if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass
        _, key, offset = query.data.split("#")
        search = FRESH.get(key)
        offset = int(offset)
        search = search.replace(' ', '_')
        btn = []
        for i in range(0, len(QUALITIES)-1, 2):
            btn.append([
                InlineKeyboardButton(
                    text=QUALITIES[i].title(),
                    callback_data=f"fq#{QUALITIES[i].lower()}#{key}#{offset}"
                ),
                InlineKeyboardButton(
                    text=QUALITIES[i+1].title(),
                    callback_data=f"fq#{QUALITIES[i+1].lower()}#{key}#{offset}"
                ),
            ])
        btn.insert(
            0,
            [
                InlineKeyboardButton(
                    text="⇊ ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ ⇊", callback_data="ident"
                )
            ],
        )
        req = query.from_user.id
        offset = 0
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"fq#homepage#{key}#{offset}")])
        await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    except Exception as e:
        print(f"Error In Quality Callback Handler - {e}")

@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, qual, key, offset = query.data.split("#")
        offset = int(offset)
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        search = FRESH.get(key)
        search = search.replace("_", " ")
        baal = qual in search
        if baal:
            search = search.replace(qual, "")
        else:
            search = search
        req = query.from_user.id
        chat_id = query.message.chat.id
        message = query.message
        try:
            if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass
        if qual != "homepage":
            search = f"{search} {qual}" 
        BUTTONS[key] = search   
        files, n_offset, total_results = await get_search_results(chat_id, search, offset=offset, filter=True)
        if not files:
            await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
            return
        temp.GETALL[key] = files
        settings = await get_settings(message.chat.id)
        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                    ),
                ]
                for file in files
            ]
            btn.insert(0, 
                [ 
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")
           
            ])

        else:
            btn = []
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [           
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")
           
            ])
        if n_offset != "":
            try:
                if settings['max_btn']:
                    btn.append(
                        [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                    )
    
                else:
                    btn.append(
                        [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                    )
            except KeyError:
                await save_group_settings(query.message.chat.id, 'max_btn', True)
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                )
        else:
            n_offset = 0
            btn.append(
                [InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")]
            )               
        if not settings.get('button'):
            cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
            time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
            remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
            cap = await get_cap(settings, remaining_seconds, files, query, total_results, search, offset)
            try:
                await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
            except MessageNotModified:
                pass
        else:
            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        await query.answer()
    except Exception as e:
        print(f"Error In Quality - {e}")

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    try:
        try:
            if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass
        _, key, offset = query.data.split("#")
        search = FRESH.get(key)
        search = search.replace(' ', '_')
        offset = int(offset)
        btn = []
        for i in range(0, len(LANGUAGES)-1, 2):
            btn.append([
                InlineKeyboardButton(
                    text=LANGUAGES[i].title(),
                    callback_data=f"fl#{LANGUAGES[i].lower()}#{key}#{offset}"
                ),
                InlineKeyboardButton(
                    text=LANGUAGES[i+1].title(),
                    callback_data=f"fl#{LANGUAGES[i+1].lower()}#{key}#{offset}"
                ),
            ])
        btn.insert(
            0,
            [
                InlineKeyboardButton(
                    text="⇊ ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ ⇊", callback_data="ident"
                )
            ],
        )
        req = query.from_user.id
        offset = 0
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"fl#homepage#{key}#{offset}")])
        await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    except Exception as e:
        print(f"Error In Language Cb Handaler - {e}")
    

@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, lang, key, offset = query.data.split("#")
        offset = int(offset)
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        search = FRESH.get(key)
        search = search.replace("_", " ")
        baal = lang in search
        if baal:
            search = search.replace(lang, "")
        else:
            search = search
        req = query.from_user.id
        chat_id = query.message.chat.id
        message = query.message
        try:
            if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass
        if lang != "homepage":
            search = f"{search} {lang}"
        BUTTONS[key] = search
        files, n_offset, total_results = await get_search_results(chat_id, search, offset=offset, filter=True)
        if not files:
            await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
            return
        temp.GETALL[key] = files
        settings = await get_settings(message.chat.id)
        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                    ),
                ]
                for file in files
            ]
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")
            
            ])
        else:
            btn = []
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")            
            ])
        if n_offset != "":
            try:
                if settings['max_btn']:
                    btn.append(
                        [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                    )
    
                else:
                    btn.append(
                        [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                    )
            except KeyError:
                await save_group_settings(query.message.chat.id, 'max_btn', True)
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                )
        else:
            n_offset = 0
            btn.append(
                [InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")]
            )    

        if not settings.get('button'):
            cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
            time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
            remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
            cap = await get_cap(settings, remaining_seconds, files, query, total_results, search, offset)
            try:
                await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            except MessageNotModified:
                pass
        else:
            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        await query.answer()
    except Exception as e:
        print(f"Error In Language - {e}")
        
@Client.on_callback_query(filters.regex(r"^seasons#"))
async def season_cb_handler(client: Client, query: CallbackQuery):
    try:
        try:
            if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass
        _, key, offset = query.data.split("#")
        search = FRESH.get(key)
        search = search.replace(' ', '_')
        offset = int(offset)
        btn = []
        for i in range(0, len(SEASONS)-1, 2):
            btn.append([
                InlineKeyboardButton(
                    text=SEASONS[i].title(),
                    callback_data=f"fs#{SEASONS[i].lower()}#{key}#{offset}"
                ),
                InlineKeyboardButton(
                    text=SEASONS[i+1].title(),
                    callback_data=f"fs#{SEASONS[i+1].lower()}#{key}#{offset}"
                ),
            ])
        btn.insert(
            0,
            [
                InlineKeyboardButton(
                    text="⇊ ꜱᴇʟᴇᴄᴛ Sᴇᴀsᴏɴ ⇊", callback_data="ident"
                )
            ],
        )
        req = query.from_user.id
        offset = 0
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"fl#homepage#{key}#{offset}")])
        await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    except Exception as e:
        print(f"Error In Season Cb Handaler - {e}")


@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_season_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, seas, key, offset = query.data.split("#")
        offset = int(offset)
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        search = FRESH.get(key)
        search = search.replace("_", " ")
        baal = seas in search
        if baal:
            search = search.replace(seas, "")
        else:
            search = search
        req = query.from_user.id
        chat_id = query.message.chat.id
        message = query.message
        try:
            if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass
        if seas != "homepage":
            search = f"{search} {seas}"
        BUTTONS[key] = search
        files, n_offset, total_results = await get_search_results(chat_id, search, offset=offset, filter=True)
        if not files:
            await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
            return
        temp.GETALL[key] = files
        settings = await get_settings(message.chat.id)
        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                    ),
                ]
                for file in files
            ]
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")

            ])
        else:
            btn = []
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            btn.insert(1, [
                InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")            
            ])
        if n_offset != "":
            try:
                if settings['max_btn']:
                    btn.append(
                        [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                    )

                else:
                    btn.append(
                        [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                    )
            except KeyError:
                await save_group_settings(query.message.chat.id, 'max_btn', True)
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{n_offset}")]
                )
        else:
            n_offset = 0
            btn.append(
                [InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")]
            )    

        if not settings.get('button'):
            cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
            time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
            remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
            cap = await get_cap(settings, remaining_seconds, files, query, total_results, search, offset)
            try:
                await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            except MessageNotModified:
                pass
        else:
            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        await query.answer()
    except Exception as e:
        print(f"Error In Season - {e}")

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movies = await get_poster(id, id=True)
    movie = movies.get('title')
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        reqstr = await bot.get_users(reqstr1)
        if NO_RESULTS_MSG:
            await bot.send_message(chat_id=BIN_CHANNEL,text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie))
        contact_admin_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔰Cʟɪᴄᴋ ʜᴇʀᴇ & ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴀᴅᴍɪɴ🔰", url=OWNER_LNK)]])
        k = await query.message.edit(script.MVE_NT_FND,reply_markup=contact_admin_button)
        await asyncio.sleep(10)
        await k.delete()
                
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    lazyData = query.data
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
    except:
        pass
    if query.data == "close_data":
        await query.message.delete()     
        
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        user = query.message.reply_to_message.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT, show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")          
                            
    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#") 
        settings = await get_settings(query.message.chat.id)
        try:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{query.message.chat.id}_{key}")
            return
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")
            
    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")

    elif query.data == "pages":
        await query.answer()    
    
    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>ꜰɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇꜱꜱ ᴡɪʟʟ ꜱᴛᴀʀᴛ ɪɴ 5 ꜱᴇᴄᴏɴᴅꜱ !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if not result.deleted_count and MULTIPLE_DB:
                        result = await Media2.collection.delete_one({
                            '_id': file_ids,
                        })
                    if result.deleted_count:
                        logger.info(f'ꜰɪʟᴇ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}! ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀꜱᴇ.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴀʀᴛᴇᴅ ꜰᴏʀ ᴅᴇʟᴇᴛɪɴɢ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ. ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword} !\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                print(f"Error In killfiledq -{e}")
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜰᴏʀ ꜰɪʟᴇ ᴅᴇʟᴇᴛᴀᴛɪᴏɴ !\n\nꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}.</b>")
    
    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings.get("button")}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings.get("button") else 'ᴛᴇxᴛ',
                                         callback_data=f'setgs#button#{settings.get("button")}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],		    
                [
                    InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],[
                    InlineKeyboardButton('ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴍᴏᴅᴇ', callback_data=f'verification_setgs#{grp_id}',),
                ],[
                    InlineKeyboardButton('ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'log_setgs#{grp_id}',),
                    InlineKeyboardButton('ꜱᴇᴛ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'caption_setgs#{grp_id}',),
                ],
                [
                    InlineKeyboardButton('⇋ ᴄʟᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                         callback_data='close_data'
                                         )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ ⚙</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)
        
    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("ᴄʜᴇᴄᴋ ᴍʏ ᴅᴍ 🗳️", url=f"telegram.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴍᴇɴᴜ ғᴏʀ {title} ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ.</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings.get("button")}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings.get("button") else 'ᴛᴇxᴛ',
                                         callback_data=f'setgs#button#{settings.get("button")}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],[
                   InlineKeyboardButton('ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴍᴏᴅᴇ', callback_data=f'verification_setgs#{grp_id}',),
                ],[
                    InlineKeyboardButton('ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'log_setgs#{grp_id}',),		
                    InlineKeyboardButton('ꜱᴇᴛ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'caption_setgs#{grp_id}',),
                ],
                [
                    InlineKeyboardButton('⇋ ᴄʟᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                         callback_data='close_data'
                                         )
                ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ ⚙</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("• ᴜᴘʟᴏᴀᴅᴇᴅ •", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("• ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"already_available#{from_user}")
             ],[
                InlineKeyboardButton("• ɴᴏᴛ ʀᴇʟᴇᴀꜱᴇᴅ •", callback_data=f"Not_Released#{from_user}"),
                InlineKeyboardButton("• Type Correct Spelling •", callback_data=f"Type_Correct_Spelling#{from_user}")
             ],[
                InlineKeyboardButton("• Not Available In The Hindi •", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
             ]]
        btn2 = [[
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [
            [InlineKeyboardButton("• ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"unalert#{from_user}")]
        ]
        btn2 = [
            [InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
            InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")]
        ]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=f"<b>Hᴇʏ {user.mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️",
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=f"<b>Hᴇʏ {user.mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>",
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
   
    elif query.data.startswith("Not_Released"):
        ident, from_user = query.data.split("#")
        btn = [[InlineKeyboardButton("📌 Not Released 📌", callback_data=f"nralert#{from_user}")]]
        btn2 = [[
            InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
            InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
        ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention}\n\n"
                        f"<code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ\n\n"
                        f"#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>Hᴇʏ {user.mention}</u>\n\n"
                        f"<b><code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ\n\n"
                        f"#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Type_Correct_Spelling"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("♨️ Type Correct Spelling ♨️", callback_data=f"wsalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Cᴏʀʀᴇᴄᴛ Sᴘᴇʟʟɪɴɢ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention}\n\n"
                        f"Wᴇ Dᴇᴄʟɪɴᴇᴅ Yᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢\n\n"
                        f"#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>Hᴇʏ {user.mention}</u>\n\n"
                        f"<b><code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢\n\n"
                        f"#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Not_Available_In_The_Hindi"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton(" Not Available In The Hindi ", callback_data=f"hnalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ Iɴ Hɪɴᴅɪ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention}\n\n"
                        f"Yᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ\n\n"
                        f"#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>Hᴇʏ {user.mention}</u>\n\n"
                        f"<b><code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ\n\n"
                        f"#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴜᴘʟᴏᴀᴅᴇᴅ •", callback_data=f"upalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uᴘʟᴏᴀᴅᴇᴅ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention},\n\n"
                        f"<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.\n"
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Uᴘʟᴏᴀᴅᴇᴅ✅"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>{content}</u>\n\n"
                        f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs."
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Uᴘʟᴏᴀᴅᴇᴅ✅\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"alalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention},\n\n"
                        f"<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\n"
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Aᴠᴀɪʟᴀʙʟᴇ 💗"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<b>Hᴇʏ {user.mention},\n\n"
                        f"<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\n"
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Aᴠᴀɪʟᴀʙʟᴇ 💗\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></i>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
            
    
    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ ✅",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Uᴘʟᴏᴀᴅᴇᴅ 🔼",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("hnalert"):
        ident, from_user = query.data.split("#")  # Hindi Not Available
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Tʜɪꜱ ɪꜱ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ❌",
                show_alert=True
            )
        else:
            await query.answer("Nᴏᴛ ᴀʟʟᴏᴡᴇᴅ — ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʀᴇǫᴜᴇꜱᴛᴇʀ ❌", show_alert=True)

    elif query.data.startswith("nralert"):
        ident, from_user = query.data.split("#")  # Not Released
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Tʜᴇ Mᴏᴠɪᴇ/ꜱʜᴏᴡ ɪꜱ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ Yᴇᴛ 🆕",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴄᴀɴ'ᴛ ᴅᴏ ᴛʜɪꜱ ᴀꜱ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ʀᴇǫᴜᴇꜱᴛᴇʀ ❌", show_alert=True)

    elif query.data.startswith("wsalert"):
        ident, from_user = query.data.split("#")  # Wrong Spelling
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇǫᴜᴇꜱᴛ ᴡᴀꜱ ʀᴇᴊᴇᴄᴛᴇᴅ ᴅᴜᴇ ᴛᴏ ᴡʀᴏɴɢ sᴘᴇʟʟɪɴɢ ❗",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇᴇ ᴛʜɪꜱ ❌", show_alert=True)

    
    elif lazyData.startswith("streamfile"):
        _, file_id = lazyData.split(":")
        try:
            user_id = query.from_user.id
            is_premium_user = await db.has_premium_access(user_id)
            if PAID_STREAM and not is_premium_user:
                premiumbtn = [[InlineKeyboardButton("𝖡𝗎𝗒 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 ♻️", callback_data='buy')]]
                await query.answer("<b>📌 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ</b>", show_alert=True)
                await query.message.reply("<b>📌 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ. ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ✅</b>", reply_markup=InlineKeyboardMarkup(premiumbtn))
                return
            username =  query.from_user.mention 
            silent_msg = await client.send_cached_media(
                chat_id=BIN_CHANNEL,
                file_id=file_id,
            )
            fileName = {quote_plus(get_name(silent_msg))}
            silent_stream = f"{URL}watch/{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            silent_download = f"{URL}{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            btn= [[
                InlineKeyboardButton("𝖲𝗍𝗋𝖾𝖺𝗆", url=silent_stream),
                InlineKeyboardButton("𝖣𝗈𝗐𝗇𝗅𝗈𝖺𝖽", url=silent_download)        
	    ]]
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
	    )
            await silent_msg.reply_text(
                text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(btn)
	    )                
        except Exception as e:
            print(e)
            await query.answer(f"⚠️ SOMETHING WENT WRONG \n\n{e}", show_alert=True)
            return
           
    
    elif query.data == "pagesn1":
        await query.answer(text=script.PAGE_TXT, show_alert=True)

    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('+ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ +', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('🧧 ᴛʀᴇɴᴅɪɴɢ ', callback_data="topsearch"),
                    InlineKeyboardButton('🎟️ ᴜᴘɢʀᴀᴅᴇ ', callback_data="premium"),
                ],[
                    #InlineKeyboardButton('♻️ ᴅᴍᴄᴀ', callback_data='disclaimer'),
                    InlineKeyboardButton('👤 ᴀʙᴏᴜᴛ ', callback_data='me')
                ],[
                    InlineKeyboardButton('🚫 ᴇᴀʀɴ ᴍᴏɴᴇʏ ᴡɪᴛʜ ʙᴏᴛ 🚫', callback_data="earn")
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
  
    elif query.data == "give_trial":
        try:
            user_id = query.from_user.id
            has_free_trial = await db.check_trial_status(user_id)
            if has_free_trial:
                await query.answer("🚸 ʏᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ᴛʀɪᴀʟ ᴏɴᴄᴇ !\n\n📌 ᴄʜᴇᴄᴋᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ ʙʏ : /plan", show_alert=True)
                return
            else:            
                await db.give_free_trial(user_id)
                await query.message.reply_text(
                    text="<b>🥳 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ\n\n🎉 ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ <u>5 ᴍɪɴᴜᴛᴇs</u> ꜰʀᴏᴍ ɴᴏᴡ !</b>",
                    quote=False,
                    disable_web_page_preview=True,                  
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💸", callback_data='seeplans')]]))
                return    
        except Exception as e:
            print(e)

    elif query.data == "premium":
        try:
            btn = [[
                InlineKeyboardButton('🧧 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ 🧧', callback_data='buy'),
            ],[
                InlineKeyboardButton('👥 ʀᴇꜰᴇʀ ꜰʀɪᴇɴᴅꜱ', callback_data='reffff'),
                #InlineKeyboardButton('🈚 ꜰʀᴇᴇ ᴛʀɪᴀʟ', callback_data='give_trial')
            ],[            
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)                        
            await client.edit_message_media(                
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))                       
            )
            await query.message.edit_text(
                text=script.BPREMIUM_TXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            print(e)

    elif query.data == "buy":
        try:
            btn = [[ 
                InlineKeyboardButton('ꜱᴛᴀʀ', callback_data='star'),
                InlineKeyboardButton('ᴜᴘɪ', callback_data='upi')
            ],[
                InlineKeyboardButton('🚫 ᴄʟᴏꜱᴇ 🚫', callback_data='close_data')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.reply_photo(
                photo=(SUBSCRIPTION),
                caption=script.PREMIUM_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            print(e)

    elif query.data == "upi":
        try:
            btn = [[ 
                InlineKeyboardButton('📱 ꜱᴇɴᴅ  ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ', url=OWNER_LNK),
            ],[
                InlineKeyboardButton('🚫 ᴄʟᴏꜱᴇ 🚫', callback_data='close_data')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.reply_photo(
                photo=(SUBSCRIPTION),
                caption=script.PREMIUM_UPI_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            print(e)

    elif query.data == "star":
        try:
            btn = [
                InlineKeyboardButton(f"{stars}⭐", callback_data=f"buy_{stars}")
                for stars, days in STAR_PREMIUM_PLANS.items()
            ]
            buttons = [btn[i:i + 2] for i in range(0, len(btn), 2)]
            buttons.append([InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data="buy")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_STAR_TEXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
	    )
        except Exception as e:
            print(e)


    elif query.data == "earn":
        try:
            btn = [[ 
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=script.EARN_INFO.format(temp.B_LINK),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            print(e)
                    
    elif query.data == "me":
        buttons = [[
            #InlineKeyboardButton ('🎁 sᴏᴜʀᴄᴇ', callback_data='source'),
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 📜', url='https://github.com/NBBotz/Auto-Filter-Bot.git'),
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='me')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "ref_point":
        await query.answer(f'You Have: {referdb.get_refer_points(query.from_user.id)} Refferal points.', show_alert=True)
    
    
    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="start")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
            )

    elif query.data.startswith("grp_pm"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
        btn = await group_setting_buttons(int(grp_id)) 
        silentx = await client.get_chat(int(grp_id))
        await query.message.edit(text=f"ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ ✅\nɢʀᴏᴜᴘ ɴᴀᴍᴇ - '{silentx.title}'</b>⚙", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("verification_setgs"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

        settings = await get_settings(int(grp_id))
        verify_status = settings.get('is_verify', IS_VERIFY)
        btn = [[
            InlineKeyboardButton(f'ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ: {"ᴏɴ" if verify_status else "ᴏꜰꜰ"}', callback_data=f'toggleverify#is_verify#{verify_status}#{grp_id}'),
	],[
            InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ', callback_data=f'changeshortner#{grp_id}'),
            InlineKeyboardButton('ᴛɪᴍᴇ', callback_data=f'changetime#{grp_id}')
	],[
            InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ', callback_data=f'changetutorial#{grp_id}')
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\nʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ꜱʜᴏʀᴛɴᴇʀ ᴠᴀʟᴜᴇꜱ ᴀɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ɢᴀᴘ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\nᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇</b>", reply_markup=InlineKeyboardMarkup(btn))
	    

    elif query.data.startswith("log_setgs"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
        btn = [[
            InlineKeyboardButton('ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'changelog#{grp_id}'),
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\nʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ᴠᴀʟᴜᴇ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\nᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇<\b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("changelog"):
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        log_channel = settings.get(f'log', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")    
        await query.message.edit(f'<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ʟᴏɢ ᴄʜᴀɴɴᴇʟ.\n\nʟᴏɢ ᴄʜᴀɴɴᴇʟ: <code>{log_channel}</code>.<b>')
        m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ɪᴅ ( ᴇxᴀᴍᴘʟᴇ: -100123569303) ᴏʀ ᴜꜱᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>") 
        while True:
            log_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
            if log_msg.text == "/cancel":
                await m.delete()
                btn = [
                    [InlineKeyboardButton('ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'changelog#{grp_id}')],
                    [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]            
                await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
                return        
            if log_msg.text.startswith("-100") and log_msg.text[4:].isdigit() and len(log_msg.text) >= 10:
                try:
                    int(log_msg.text)
                    break 
                except ValueError:
                    await query.message.reply("<b>ɪɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ! ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ ꜱᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ -100 (ᴇxᴀᴍᴘʟᴇ: -100123456789)</b>")
            else:       
                await query.message.reply("<b>ɪɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ! ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ ꜱᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ -100 (ᴇxᴀᴍᴘʟᴇ: -100123456789)</b>")		
        await m.delete()	
        await save_group_settings(int(grp_id), f'log', log_msg.text)
        await client.send_message(LOG_API_CHANNEL, f"#Set_Log_Channel\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {silentx.title}\n\nɢʀᴏᴜᴘ ɪᴅ: {grp_id}\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {query.from_user.username}")	    
        btn = [            
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ᴠᴀʟᴜᴇ ✅\nʟᴏɢ ᴄʜᴀɴɴᴇʟ: <code>{log_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("caption_setgs"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        btn = [[
            InlineKeyboardButton('ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'changecaption#{grp_id}'),
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\nʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴠᴀʟᴜᴇꜱ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\nᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("changecaption"):
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        current_caption = settings.get(f'caption', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")    
        await query.message.edit(f'<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.\n\nᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ: <code>{current_caption}</code>.</b>')
        m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ\n\nᴄᴀᴘᴛɪᴏɴ ꜰᴏʀᴍᴀᴛ:\nꜰɪʟᴇ ɴᴀᴍᴇ -<code>{file_name}</code>\nꜰɪʟᴇ ᴄᴀᴘᴛɪᴏɴ - <code>{file_caption}</code>\n<code>ꜰɪʟᴇ ꜱɪᴢᴇ - {file_size}</code>\n\nᴏʀ ᴜꜱᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>") 
        caption_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if caption_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'changecaption#{grp_id}'),
	    ],[
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await m.delete()
            return
        await m.delete()	
        await save_group_settings(int(grp_id), f'caption', caption_msg.text)
        await client.send_message(LOG_API_CHANNEL, f"#Set_Caption\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {title}\n\nɢʀᴏᴜᴘ ɪᴅ: {grp_id}\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {query.from_user.username}")	    
        btn = [            
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴠᴀʟᴜᴇꜱ ✅\n\nᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ: <code>{caption_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))

	
    elif query.data.startswith("toggleverify"):
        _, set_type, status, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)    
        new_status = not (status == "True")
        await save_group_settings(int(grp_id), set_type, new_status)
        settings = await get_settings(int(grp_id))
        verify_status = settings.get('is_verify', IS_VERIFY)
        btn = [[
            InlineKeyboardButton(f'ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ: {"ᴏɴ" if verify_status else "ᴏꜰꜰ"}', callback_data=f'toggleverify#is_verify#{verify_status}#{grp_id}'),
	],[
            InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ', callback_data=f'changeshortner#{grp_id}'),
            InlineKeyboardButton('ᴛɪᴍᴇ', callback_data=f'changetime#{grp_id}')
	],[
            InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ', callback_data=f'changetutorial#{grp_id}')
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\nʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ꜱʜᴏʀᴛɴᴇʀ ᴠᴀʟᴜᴇꜱ ᴀɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ɢᴀᴘ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\nᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇</b>", reply_markup=InlineKeyboardMarkup(btn))


    elif query.data.startswith("changeshortner"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        btn = [
            [
                InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 1', callback_data=f'set_verify1#{grp_id}'),
                InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 2', callback_data=f'set_verify2#{grp_id}')
            ],
            [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 3', callback_data=f'set_verify3#{grp_id}')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ꜱʜᴏʀᴛɴᴇʀ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_verify"):
        shortner_num = query.data.split("#")[0][-1]
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        suffix = "" if shortner_num == "1" else f"_{'two' if shortner_num == '2' else 'three'}"
        current_url = settings.get(f'shortner{suffix}', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")
        current_api = settings.get(f'api{suffix}', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")    
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ꜱʜᴏʀᴛɴᴇʀ {shortner_num}:\nᴡᴇʙꜱɪᴛᴇ: <code>{current_url}</code>\nᴀᴘɪ: <code>{current_api}</code></b>")
        m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ᴏʀ ᴜꜱᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>") 
        url_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if url_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 1', callback_data=f'set_verify1#{grp_id}'),
                InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 2', callback_data=f'set_verify2#{grp_id}')
            ],
            [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 3', callback_data=f'set_verify3#{grp_id}')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ꜱʜᴏʀᴛɴᴇʀ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await m.delete()
            return
        await m.delete()
        n = await query.message.reply("<b>ɴᴏᴡ ꜱᴇɴᴅ ꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ ᴏʀ ᴜꜱᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>")
        key_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if key_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 1', callback_data=f'set_verify1#{grp_id}'),
                InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 2', callback_data=f'set_verify2#{grp_id}')
            ],
            [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 3', callback_data=f'set_verify3#{grp_id}')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ꜱʜᴏʀᴛɴᴇʀ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await n.delete()
            return
        await n.delete()    		
        await save_group_settings(int(grp_id), f'shortner{suffix}', url_msg.text)
        await save_group_settings(int(grp_id), f'api{suffix}', key_msg.text)
        log_message = f"#New_Shortner_Set\n\n ꜱʜᴏʀᴛɴᴇʀ ɴᴏ - {shortner_num}\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{invite_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`\nᴀᴅᴅᴇᴅ ʙʏ - `{user_id}`\nꜱʜᴏʀᴛɴᴇʀ ꜱɪᴛᴇ - {url_msg.text}\nꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ - `{key_msg.text}`"
        await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
        next_shortner = int(shortner_num) + 1 if shortner_num in ["1", "2"] else None
        btn = [
            [InlineKeyboardButton(f'ꜱʜᴏʀᴛɴᴇʀ {next_shortner}', callback_data=f'set_verify{next_shortner}#{grp_id}')] if next_shortner else [],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ꜱʜᴏʀᴛɴᴇʀ {shortner_num} ᴠᴀʟᴜᴇꜱ ✅\n\nᴡᴇʙꜱɪᴛᴇ: <code>{url_msg.text}</code>\nᴀᴘɪ: <code>{key_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))

    
    elif query.data.startswith("changetime"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        btn = [
            [
                InlineKeyboardButton('2ɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ', callback_data=f'set_time2#{grp_id}'),
	    ],[
                InlineKeyboardButton('3ʀᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ', callback_data=f'set_time3#{grp_id}')
            ],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ɢᴀᴘ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_time"):
        time_num = query.data.split("#")[0][-1]
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        suffix = "" if time_num == "2" else "third_" if time_num == "3" else ""
        current_time = settings.get(f'{suffix}verify_time', 'Not set')
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ {time_num} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ:\n\nᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ: {current_time}</b>")
        m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ ᴏʀ ᴜꜱᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ.</b>")        
        while True:
            time_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
            if time_msg.text == "/cancel":
                await m.delete()
                btn = [
                    [InlineKeyboardButton('2ɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ', callback_data=f'set_time2#{grp_id}')],
                    [InlineKeyboardButton('3ʀᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ', callback_data=f'set_time3#{grp_id}')],
                    [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]   
                await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
                return        
            if time_msg.text.isdigit() and int(time_msg.text) > 0:
                break
            else:
                await query.message.reply("<b>ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ! ᴍᴜꜱᴛ ʙᴇ ᴀ ᴘᴏꜱɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ (ᴇxᴀᴍᴘʟᴇ: 60)</b>")
        await m.delete()
        await save_group_settings(int(grp_id), f'{suffix}verify_time', time_msg.text)
        log_message = f"#New_Time_Set\n\n ᴛɪᴍᴇ ɴᴏ - {time_num}\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{invite_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`\nᴀᴅᴅᴇᴅ ʙʏ - `{user_id}`\nᴛɪᴍᴇ - {time_msg.text}"
        await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
        next_time = int(time_num) + 1 if time_num in ["2"] else None
        btn = [
            [InlineKeyboardButton(f'{next_time} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ', callback_data=f'set_time{next_time}#{grp_id}')] if next_time else [],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>{time_num} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ᴜᴘᴅᴀᴛᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\nᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ: {time_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("changetutorial"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        btn = [
            [
                InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 1', callback_data=f'set_tutorial1#{grp_id}'),
                InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 2', callback_data=f'set_tutorial2#{grp_id}')
            ],
            [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 3', callback_data=f'set_tutorial3#{grp_id}')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴛᴜᴛᴏʀɪᴀʟ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_tutorial"):
        tutorial_num = query.data.split("#")[0][-1]
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        suffix = "" if tutorial_num == "1" else f"_{'2' if tutorial_num == '2' else '3'}"
        tutorial_url = settings.get(f'tutorial{suffix}', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")    
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num}:\n\nᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ: {tutorial_url}.</b>")
        m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ ᴏʀ ᴜꜱᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>") 
        tutorial_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if tutorial_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 1', callback_data=f'set_tutorial1#{grp_id}'),
                InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 2', callback_data=f'set_tutorial2#{grp_id}')
            ],
            [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 3', callback_data=f'set_tutorial3#{grp_id}')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴛᴜᴛᴏʀɪᴀʟ ᴀɴᴅ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴠᴀʟᴜᴇꜱ ᴀꜱ ʏᴏᴜ ᴡᴀɴᴛ ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await m.delete()
            return
        await m.delete()	
        await save_group_settings(int(grp_id), f'tutorial{suffix}', tutorial_msg.text)
        log_message = f"#New_Tutorial_Set\n\n ᴛᴜᴛᴏʀɪᴀʟ ɴᴏ - {tutorial_num}\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{invite_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`\nᴀᴅᴅᴇᴅ ʙʏ - `{user_id}`\nᴛᴜᴛᴏʀɪᴀʟ - {tutorial_msg.text}"
        await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
        next_tutorial = int(tutorial_num) + 1 if tutorial_num in ["1", "2"] else None
        btn = [
            [InlineKeyboardButton(f'ᴛᴜᴛᴏʀɪᴀʟ {next_tutorial}', callback_data=f'set_tutorial{next_tutorial}#{grp_id}')] if next_tutorial else [],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num} ᴠᴀʟᴜᴇꜱ ✅\n\nᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ: {tutorial_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))
	    
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer(script.ALRT_TXT, show_alert=True)
            return
        if status == "True":
            await save_group_settings(int(grp_id), set_type, False)
            await query.answer("ᴏꜰꜰ ✗")
        else:
            await save_group_settings(int(grp_id), set_type, True)
            await query.answer("ᴏɴ ✓")
        settings = await get_settings(int(grp_id))
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings.get("button")}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings.get("button") else 'ᴛᴇxᴛ',
                                         callback_data=f'setgs#button#{settings.get("button")}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],[
                   InlineKeyboardButton('ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴍᴏᴅᴇ', callback_data=f'verification_setgs#{grp_id}',),
                ],[
                    InlineKeyboardButton('ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'log_setgs#{grp_id}',),
                    InlineKeyboardButton('ꜱᴇᴛ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'caption_setgs#{grp_id}',),
                ],
                [
                    InlineKeyboardButton('⇋ ᴄʟᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                         callback_data='close_data'
                                         )
                ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)

    
async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if not spoll:
        message = msg
        if message.text.startswith("/"): return
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = message.text         
            search = search.lower()
            m=await message.reply_text(f'<b>Wᴀɪᴛ {message.from_user.mention} Sᴇᴀʀᴄʜɪɴɢ Yᴏᴜʀ Qᴜᴇʀʏ :<i>{search}...</i></b>', reply_to_message_id=message.id)
            find = search.split(" ")
            search = ""
            removes = ["in","upload", "series", "full", "horror", "thriller", "mystery", "print", "file"]
            for x in find:
                if x in removes:
                    continue
                else:
                    search = search + x + " "
            search = search.replace("-", " ")
            search = search.replace(":","")
            search = re.sub(r'\s+', ' ', search).strip()
            files, offset, total_results = await get_search_results(message.chat.id ,search, offset=0, filter=True)
            settings = await get_settings(message.chat.id)
            if not files:
                if settings["spell_check"]:
                    ai_sts = await m.edit('🤖 ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ, ᴀɪ ɪꜱ ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ...')
                    is_misspelled = await ai_spell_check(chat_id = message.chat.id,wrong_name=search)
                    if is_misspelled:
                        await ai_sts.edit(f'<b>✅Aɪ Sᴜɢɢᴇsᴛᴇᴅ ᴍᴇ<code> {is_misspelled}</code> \nSᴏ Iᴍ Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ <code>{is_misspelled}</code></b>')
                        await asyncio.sleep(2)
                        message.text = is_misspelled
                        await ai_sts.delete()
                        return await auto_filter(client, message)
                    await ai_sts.delete()
                    return await advantage_spell_chok(client, message)
        else:
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
        m=await message.reply_text(f'<b>Wᴀɪᴛ {message.from_user.mention} Sᴇᴀʀᴄʜɪɴɢ Yᴏᴜʀ Qᴜᴇʀʏ :<i>{search}...</i></b>', reply_to_message_id=message.id)
        settings = await get_settings(message.chat.id)
        await msg.message.delete()
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = search
    temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                ),
            ]
            for file in files
        ]
        btn.insert(0, 
            [
                InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
            ]
        )
        btn.insert(1, [
            InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")
            
        ])
    else:
        btn = []
        btn.insert(0, 
            [
                InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
            ]
        )
        btn.insert(1, [
            InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")
            
        ])
    if offset != "":
        req = message.from_user.id if message.from_user else 0
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    TEMPLATE = script.IMDB_TEMPLATE_TXT
    if imdb:
        cap = TEMPLATE.format(
            qurey=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
        temp.IMDB_CAP[message.from_user.id] = cap
        if not settings.get('button'):
            for file_num, file in enumerate(files, start=1):
                cap += f"\n\n<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}</a></b>"
    else:
        if settings.get('button'):
            cap =f"<b><blockquote>Hᴇʏ,{message.from_user.mention}</blockquote>\n\n📂 Hᴇʀᴇ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"
        else:
            cap =f"<b><blockquote>Hᴇʏ,{message.from_user.mention}</blockquote>\n\n📂 Hᴇʀᴇ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"            
            for file_num, file in enumerate(files, start=1):
                cap += f"<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}\n\n</a></b>"                
    if imdb and imdb.get('poster'):
        try:
            hehe = await m.edit_photo(photo=imdb.get('poster'), caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await hehe.delete()
                    await message.delete()
            except KeyError:
                await save_group_settings(message.chat.id, 'auto_delete', True)
                await asyncio.sleep(DELETE_TIME)
                await hehe.delete()
                await message.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg") 
            hmm = await m.edit_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            try:
               if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await hmm.delete()
                    await message.delete()
            except KeyError:
                await save_group_settings(message.chat.id, 'auto_delete', True)
                await asyncio.sleep(DELETE_TIME)
                await hmm.delete()
                await message.delete()
        except Exception as e:
            logger.exception(e)
            fek = await m.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await fek.delete()
                    await message.delete()
            except KeyError:
                await save_group_settings(message.chat.id, 'auto_delete', True)
                await asyncio.sleep(DELETE_TIME)
                await fek.delete()
                await message.delete()
    else:
        fuk = await m.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
        try:
            if settings['auto_delete']:
                await asyncio.sleep(DELETE_TIME)
                await fuk.delete()
                await message.delete()
        except KeyError:
            await save_group_settings(message.chat.id, 'auto_delete', True)
            await asyncio.sleep(DELETE_TIME)
            await fuk.delete()
            await message.delete()

async def ai_spell_check(chat_id, wrong_name):
    async def search_movie(wrong_name):
        search_results = imdb.search_movie(wrong_name)
        movie_list = [movie['title'] for movie in search_results]
        return movie_list
    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return 
        movie = closest_match[0]
        files, offset, total_results = await get_search_results(chat_id=chat_id, query=movie)
        if files:
            return movie
        movie_list.remove(movie)

async def advantage_spell_chok(client, message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(search, bulk=True)
    except:
        k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    if not movies:
        google = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")
        ]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[
        InlineKeyboardButton(text=movie.get('title'), callback_data=f"spol#{movie.movieID}#{user}")
    ]
        for movie in movies
    ]
    buttons.append(
        [InlineKeyboardButton(text="🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data')]
    )
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(60)
    await d.delete()
    try:
        await message.delete()
    except:
        pass
