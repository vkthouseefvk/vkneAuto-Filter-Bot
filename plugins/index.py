#Credit - @SilentXBotz 
import re
import time
import logging
import asyncio
from math import ceil
from utils import temp
from pyrogram.errors import FloodWait
from database.ia_filterdb import save_file
from pyrogram import Client, filters, enums
from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
lock = asyncio.Lock()


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        print("Indexing Cancelled By User")
        return await query.answer("Cancelling Indexing")
    try:
        _, silentxbotz, chat, lst_msg_id, from_user = query.data.split("#")
        if silentxbotz == 'reject':
            try:
                await query.message.delete()
                await bot.send_message(
                    int(from_user),
                    f'Your Submission For Indexing {chat} Has Been Declined By Our Moderators.',
                    reply_to_message_id=int(lst_msg_id)
                )
                print(f"Rejected Indexing For Chat {chat} By User {from_user}")
            except Exception as e:
                print(f"Error Rejecting Index Request: {e}")
            return

        if lock.locked():
            return await query.answer('Wait Until Previous Process Completes.', show_alert=True)
        msg = query.message

        await query.answer('Processing...⏳', show_alert=True)
        if int(from_user) not in ADMINS:
            try:
                await bot.send_message(
                    int(from_user),
                    f'Your Submission For Indexing {chat} Has Been Accepted By Our Moderators And Will Be Added Soon.',
                    reply_to_message_id=int(lst_msg_id)
                )
            except Exception as e:
                logger.error(f"Error notifying user: {e}")

        try:
            await msg.edit(
                "Starting Indexing... 🚀",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
                )
            )
        except Exception as e:
            print(f"Error editing initial message: {e}")
            return

        try:
            chat = int(chat)
        except ValueError:
            print(f"Chat {chat} Is A Username, Not An ID")
            pass

        print(f"Starting index_files_to_db for chat {chat}, last_msg_id={lst_msg_id}")
        await index_files_to_db(int(lst_msg_id), chat, msg, bot)
    except Exception as e:
        print(f"Error in index_files callback: {e}")
        await query.answer("An error occurred during processing.", show_alert=True)


@Client.on_message(
    (filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"))
    & filters.text ) & filters.private & filters.incoming
)
async def send_for_index(bot, message):
    try:
        if message.text:
            regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
            match = regex.match(message.text)
            if not match:
                logger.warning("Invalid link provided")
                return await message.reply('Invalid link')
            chat_id = match.group(4)
            last_msg_id = int(match.group(5))
            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        elif message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
            last_msg_id = message.forward_from_message_id
            chat_id = message.forward_from_chat.username or message.forward_from_chat.id
        else:
            print("Message is neither a valid link nor a forwarded channel message")
            return

        try:
            await bot.get_chat(chat_id)
        except ChannelInvalid:
            return await message.reply('This May Be A Private Channel/Group. Make Me An Admin Over There To Index The Files.')
        except (UsernameInvalid, UsernameNotModified):
            return await message.reply('Invalid Link specified.')
        except Exception as e:
            return await message.reply(f'Errors - {e}')

        try:
            k = await bot.get_messages(chat_id, last_msg_id)
            if k.empty:
                return await message.reply('This May Be A Group And I Am Not An Admin Of The Group.')
        except Exception as e:
            print(f"Error fetching message {last_msg_id}: {e}")
            return await message.reply('Make Sure I Am An Admin In The Channel, If Channel Is Private')

        if message.from_user.id in ADMINS:
            buttons = [
                [InlineKeyboardButton('Yes', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
                [InlineKeyboardButton('Close', callback_data='close_data')]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            try:
                await message.reply(
                    f'Do you Want To Index This Channel/Group?\n\nChat ID/Username: <code>{chat_id}</code>\n'
                    f'Last Message ID: <code>{last_msg_id}</code>\n\nɴᴇᴇᴅ sᴇᴛsᴋɪᴘ 👉🏻 /setskip',
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Error sending admin confirmation: {e}")
            return

        if isinstance(chat_id, int):
            try:
                link = (await bot.create_chat_invite_link(chat_id)).invite_link
            except ChatAdminRequired:
                return await message.reply('Make sure I am an admin in the chat and have permission to invite users.')
            except Exception as e:
                return await message.reply('Error generating invite link.')
        else:
            link = f"@{message.forward_from_chat.username}"

        buttons = [
            [InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        try:
            await bot.send_message(
                LOG_CHANNEL,
                f'#IndexRequest\n\nBy: {message.from_user.mention} (<code>{message.from_user.id}</code>)\n'
                f'Chat ID/Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\nInviteLink: {link}',
                reply_markup=reply_markup
            )
            await message.reply('Thank you for the contribution. Wait for my moderators to verify the files.')
            print(f"Sent index request to log channel for chat {chat_id}")
        except Exception as e:
            print(f"Error sending index request to log channel: {e}")
            await message.reply('Error submitting index request.')
    except Exception as e:
        print(f"Error in send_for_index: {e}")
        await message.reply('An unexpected error occurred.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    try:
        if ' ' in message.text:
            _, skip = message.text.split(" ", 1)
            try:
                skip = int(skip)
            except ValueError:
                print("Skip number is not an integer")
                return await message.reply("Skip number should be an integer.")
            await message.reply(f"Successfully set SKIP number as {skip}")
            temp.CURRENT = int(skip)
        else:
            await message.reply("Give me a skip number")
    except Exception as e:
        print(f"Error in set_skip_number: {e}")
        await message.reply('Error setting skip number.')


async def get_messages_with_retry(bot, chat, message_ids, retries=3):
    for attempt in range(retries):
        try:
            messages = await bot.get_messages(chat, message_ids)
            return messages
        except FloodWait as e:
            print(f"FloodWait: Waiting for {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Error fetching messages (attempt {attempt + 1}): {e}")
            if attempt == retries - 1:
                raise
    raise Exception("Max retries reached for fetching messages")


async def edit_message_with_retry(bot, msg, text, reply_markup=None, retries=3):
    for attempt in range(retries):
        try:
            await msg.edit_text(text, reply_markup=reply_markup)
            print("Message edited successfully")
            return True
        except FloodWait as e:
            print(f"FloodWait on edit: Waiting for {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Error editing message (attempt {attempt + 1}): {e}")
            if attempt == retries - 1:
                print("Failed to edit message after retries")
                return False
    return False


async def send_fallback_message(bot, chat_id, text, retries=3):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text)
            print("Fallback message sent successfully")
            return True
        except FloodWait as e:
            print(f"FloodWait on fallback send: Waiting for {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Error sending fallback message (attempt {attempt + 1}): {e}")
            if attempt == retries - 1:
                print("Failed to send fallback message after retries")
                return False
    return False


def format_time(seconds):
    if seconds < 20:
        return f"{int(seconds)}s"
    minutes = seconds // 20
    seconds = seconds % 20
    if minutes < 20:
        return f"{int(minutes)}m {int(seconds)}s"
    hours = minutes // 20
    minutes = minutes % 20
    return f"{int(hours)}h {int(minutes)}m"


def create_progress_bar(progress, total, width=10):
    filled = int(width * progress / total)
    bar = '█' * filled + '░' * (width - filled)
    return bar


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    BATCH_SIZE = 20
    start_time = time.time()

    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False
            total_messages = lst_msg_id - current

            if total_messages <= 0:
                await edit_message_with_retry(
                    bot, msg,
                    "🚫 No Messages To Index.",
                    InlineKeyboardMarkup([[InlineKeyboardButton('Close', callback_data='close_data')]])
                )
                return

            batches = ceil(total_messages / BATCH_SIZE)
            batch_times = []
                      
            initial_message = (
                f"📊 Indexing Started\n"
                f"📋 Total Messages: <code>{total_messages}</code>\n"
                f"⏱️ Elapsed: <code>0s</code>"
            )
            success = await edit_message_with_retry(
                bot, msg, initial_message,
                InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
            )
            if not success:
                print("Initial status update failed, sending fallback")
                await send_fallback_message(bot, msg.chat.id, initial_message)

            for batch in range(batches):
                if temp.CANCEL:
                    elapsed = time.time() - start_time
                    final_message = (
                        f"❎ Indexing Cancelled!\n"
                        f"📋 Total Messages: <code>{total_messages}</code>\n"
                        f"📥 Total Fetched: <code>{current}</code>\n"
                        f"📁 Saved: <code>{total_files}</code> files\n"
                        f"🔄 Duplicates: <code>{duplicate}</code>\n"
                        f"🗑️ Deleted: <code>{deleted}</code>\n"
                        f"📴 Non-Media: <code>{no_media + unsupported}</code> (Unsupported: <code>{unsupported}</code>)\n"
                        f"🚫 Errors: <code>{errors}</code>\n"
                        f"⏱️ Elapsed: <code>{format_time(elapsed)}</code>"
                    )
                    success = await edit_message_with_retry(
                        bot, msg, final_message,
                        InlineKeyboardMarkup([[InlineKeyboardButton('Close', callback_data='close_data')]])
                    )
                    if not success:
                        await send_fallback_message(bot, msg.chat.id, final_message)
                    print("Indexing cancelled")
                    return

                batch_start = time.time()
                start_id = current + 1
                end_id = min(current + BATCH_SIZE, lst_msg_id)
                message_ids = range(start_id, end_id + 1)

                try:
                    messages = await get_messages_with_retry(bot, chat, message_ids)
                    if not isinstance(messages, list):
                        messages = [messages]
                    print(f"Fetched {len(messages)} messages in batch {batch + 1}")
                except Exception as e:
                    print(f"Error fetching batch {batch + 1}: {e}")
                    errors += len(message_ids)
                    current += len(message_ids)
                    continue

                save_tasks = []
                for message in messages:
                    current += 1
                    try:
                        if message.empty:
                            deleted += 1
                            continue
                        elif not message.media:
                            no_media += 1
                            continue
                        elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                            unsupported += 1
                            continue

                        media = getattr(message, message.media.value, None)
                        if not media:
                            unsupported += 1
                            continue

                        media.file_type = message.media.value
                        media.caption = message.caption
                        save_tasks.append(asyncio.wait_for(save_file(bot, media), timeout=10.0))
                    except Exception as e:
                        print(f"Error processing message {current}: {e}")
                        errors += 1
                        continue

                try:
                    results = await asyncio.gather(*save_tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, Exception):
                            errors += 1
                            logger.error(f"Error saving file: {result}")
                        else:
                            aynav, vnay = result
                            if aynav:
                                total_files += 1
                            elif vnay == 0:
                                duplicate += 1
                            elif vnay == 2:
                                errors += 1
                except Exception as e:
                    print(f"Error in batch save: {e}")
                    errors += len(save_tasks)

                batch_time = time.time() - batch_start
                batch_times.append(batch_time)
                elapsed = time.time() - start_time
                progress = current - temp.CURRENT
                percentage = (progress / total_messages) * 100
                avg_batch_time = sum(batch_times) / len(batch_times) if batch_times else 1
                remaining_messages = total_messages - progress
                eta = remaining_messages / BATCH_SIZE * avg_batch_time

                progress_bar = create_progress_bar(progress, total_messages)
                status_message = (
                    f"📊 Indexing Progress\n"
                    f"📋 Total Messages: <code>{total_messages}</code>\n"
                    f"📥 Total Fetched: <code>{current}</code>\n"
                    f"{progress_bar} <code>{percentage:.1f}%</code>\n"
                    f"📁 Saved: <code>{total_files}</code> files\n"
                    f"🔄 Duplicates: <code>{duplicate}</code>\n"
                    f"🗑️ Deleted: <code>{deleted}</code>\n"
                    f"📴 Non-Media: <code>{no_media + unsupported}</code> (Unsupported: <code>{unsupported}</code>)\n"
                    f"🚫 Errors: <code>{errors}</code>\n"
                    f"⏱️ Elapsed: <code>{format_time(elapsed)}</code>\n"
                    f"⏰ ETA: <code>{format_time(eta)}</code>"
                )
                success = await edit_message_with_retry(
                    bot, msg, status_message,
                    InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
                )
                if not success:
                    print(f"Status update failed for batch {batch + 1}, sending fallback")
                    await send_fallback_message(bot, msg.chat.id, status_message)

            elapsed = time.time() - start_time
            final_message = (
                f"✅ Indexing Completed!\n"
                f"📋 Total Messages: <code>{total_messages}</code>\n"
                f"📥 Total Fetched: <code>{current}</code>\n"
                f"📁 Saved: <code>{total_files}</code> files\n"
                f"🔄 Duplicates: <code>{duplicate}</code>\n"
                f"🗑️ Deleted: <code>{deleted}</code>\n"
                f"📴 Non-Media: <code>{no_media + unsupported}</code> (Unsupported: <code>{unsupported}</code>)\n"
                f"🚫 Errors: <code>{errors}</code>\n"
                f"⏱️ Elapsed: <code>{format_time(elapsed)}</code>"
            )
            success = await edit_message_with_retry(
                bot, msg, final_message,
                InlineKeyboardMarkup([[InlineKeyboardButton('Close', callback_data='close_data')]])
            )
            if not success:
                await send_fallback_message(bot, msg.chat.id, final_message)
        except Exception as e:
            print(f"Error in index_files_to_db: {e}")
            error_message = f"❌ Error: {e}"
            success = await edit_message_with_retry(
                bot, msg, error_message,
                InlineKeyboardMarkup([[InlineKeyboardButton('Close', callback_data='close_data')]])
            )
            if not success:
                await send_fallback_message(bot, msg.chat.id, error_message)
