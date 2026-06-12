import os
import re
import asyncio
import random
import time
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

API_ID = 123456 #replace_with_your_api_id
API_HASH = "vwksdbhkvbekrvrii5" #replace_with_your_api_hash

SESSION_NAME = "chatbot_session"
TEMP_DIR = "temp_processing"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def parse_telegram_link(url: str):
    url = url.strip()
    private_match = re.search(r"t\.me/c/(\d+)/(?:\d+/)?(\d+)", url)
    if private_match:
        raw_chat_id = private_match.group(1)
        msg_id = int(private_match.group(2))
        chat_id = int(f"-100{raw_chat_id}") if not raw_chat_id.startswith("-100") else int(raw_chat_id)
        return chat_id, msg_id

    public_match = re.search(r"t\.me/([^/]+)/(?:\d+/)?(\d+)", url)
    if public_match:
        return public_match.group(1), int(public_match.group(2))

    return None, None
  
class ProgressBar:
    def __init__(self, status_msg, base_text):
        self.status_msg = status_msg
        self.base_text = base_text
        self.last_update_time = 0

    async def __call__(self, current, total):
        if not total:
            return
            
        now = time.time()
        if now - self.last_update_time > 3.0 or current == total:
            self.last_update_time = now
            percentage = (current / total) * 100
            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            
            bar_length = 15
            filled = int(bar_length * current // total)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            text = f"{self.base_text}\n[{bar}] {percentage:.1f}%\n{current_mb:.2f} MB / {total_mb:.2f} MB"
            
            if current == total: #ps
                text += "\n✅ 100% Completed!"
            
            try:
                await self.status_msg.edit(text)
            except Exception:
                pass 

async def process_single_media(chat_peer, message_id: int, status_msg, original_link: str, header_text=""):
    local_file_path = None
    thumb_path = None  
    try:
        source_msg = await client.get_messages(chat_peer, ids=message_id)
        
        if not source_msg:
            await client.send_message('me', f"{header_text}❌ Message not found for ID: {message_id}")
            return False
            
        if not source_msg.media:
            if source_msg.text:
                await client.send_message('me', f"{header_text}{source_msg.text}\n\n*🔗 Source: {original_link}*")
                return True
            else:
                await client.send_message('me', f"{header_text}❌ Empty message at ID: {message_id} (Skipping)")
                return False

        dl_progress = ProgressBar(status_msg, f"{header_text}📥 Downloading ID {message_id}...")
        local_file_path = await client.download_media(source_msg, file=TEMP_DIR, progress_callback=dl_progress)
        
        if not local_file_path or not os.path.exists(local_file_path):
            await client.send_message('me', f"{header_text}❌ Local write failure for ID: {message_id}")
            return False

        is_video = bool(getattr(source_msg, 'video', False) or (source_msg.document and source_msg.document.mime_type and source_msg.document.mime_type.startswith('video/')))
        is_photo = bool(getattr(source_msg, 'photo', False))
        original_caption = source_msg.text if source_msg.text else ""
        original_attributes = getattr(source_msg.document, 'attributes', None)
        
        upload_kwargs = {
            'entity': 'me',
            'file': local_file_path,
            'caption': f"{original_caption}\n\n*🔗 Source: {original_link}*",
            'progress_callback': ProgressBar(status_msg, f"{header_text}📤 Uploading ID {message_id}..."),
            'attributes': original_attributes
        }
        
        if is_video and getattr(source_msg.document, 'thumbs', None):
            try:
                thumb_path = await client.download_media(source_msg.document, thumb=-1, file=TEMP_DIR)
                if thumb_path:
                    upload_kwargs['thumb'] = thumb_path
            except Exception:
                pass 
        if is_video:
            upload_kwargs['supports_streaming'] = True
            upload_kwargs['force_document'] = False
        elif is_photo:
            upload_kwargs['force_document'] = False
        else:
            upload_kwargs['force_document'] = True

        # 6. Mirror Transmission
        await client.send_file(**upload_kwargs)
        return True

    except FloodWaitError as e:
        await client.send_message('me', f"{header_text}⚠️ Rate limit hit. Forced pause for {e.seconds}s.")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        await client.send_message('me', f"{header_text}❌ Error on ID {message_id}: {str(e)}")
        return False
    finally:
        # Cleanup both the main file and the thumbnail
        for path in [local_file_path, thumb_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

@client.on(events.NewMessage(chats='me'))
async def master_listener(event):
    text = event.raw_text.strip()
    
    if text.lower().startswith("/start"):
        await event.respond(
            "🤖 **Welcome to your Local Mirror Bot!**\n\n"
            "I am running natively on your machine with `.mkv` cloning active.\n\n"
            "**📘 Single Link Mode**\n"
            "Paste any raw Telegram link directly.\n\n"
            "**📦 Batch Download Mode**\n"
            "Use: `batch [start_link] [end_link]`\n\n"
            "**🔗 Multilink Mode**\n"
            "Use: `multilink` followed by text blocks containing your links."
        )
        return

    elif text.lower().startswith("batch"):
        links = re.findall(r"https?://t\.me/[^\s]+", text)
        if len(links) < 2:
            await event.respond("❌ Error: Batch requires both a START and an END link.")
            return
            
        start_chat, start_id = parse_telegram_link(links[0])
        end_chat, end_id = parse_telegram_link(links[1])
        
        if None in (start_chat, start_id, end_chat, end_id) or start_chat != end_chat:
            await event.respond("❌ Error: Invalid links or links point to different channels.")
            return
            
        if start_id > end_id:
            start_id, end_id = end_id, start_id
            
        total_items = (end_id - start_id) + 1
        status = await event.respond(f"🔄 Preparing Batch Processing ({total_items} items)...")
        
        current_index = 1
        for current_id in range(start_id, end_id + 1):
            remaining = total_items - current_index
            header = f"**📦 Item {current_index} of {total_items} ({remaining} remaining)**\n"
            
            mock_link = f"https://t.me/c/{str(start_chat).replace('-100', '')}/{current_id}"
            await process_single_media(start_chat, current_id, status, mock_link, header)
            
            if current_index != total_items:
                await status.edit(f"{header}⏳ Anti-ban cooldown active... pausing briefly.")
                await asyncio.sleep(random.uniform(8.0, 15.0))
            current_index += 1
                
        await status.edit("✅ **Sequential Batch processing complete.**")
        return

    elif text.lower().startswith("multilink"):
        links = re.findall(r"https?://t\.me/[^\s]+", text)
        unique_links = list(dict.fromkeys(links))
        
        if not unique_links:
            await event.respond("❌ No valid Telegram links detected.")
            return
            
        total_items = len(unique_links)
        status = await event.respond(f"🔄 Preparing Multilink Processing ({total_items} items)...")
        
        for index, url in enumerate(unique_links, start=1):
            remaining = total_items - index
            header = f"**🔗 Item {index} of {total_items} ({remaining} remaining)**\n"
            
            chat_peer, msg_id = parse_telegram_link(url)
            if chat_peer is not None and msg_id is not None:
                await process_single_media(chat_peer, msg_id, status, url, header)
            
            if index != total_items:
                await status.edit(f"{header}⏳ Anti-ban cooldown active... pausing briefly.")
                await asyncio.sleep(random.uniform(8.0, 15.0))
                
        await status.edit("✅ **Multilink block processing complete.**")
        return #ps

    elif text.startswith("https://t.me/"):
        status = await event.respond("🔄 Validating Single Link...")
        chat_peer, msg_id = parse_telegram_link(text)
        
        if chat_peer is not None and msg_id is not None:
            success = await process_single_media(chat_peer, msg_id, status, text)
            if success:
                await status.delete()
            else:
                await status.edit("❌ Mirror failed or message held no media.")
        return

if __name__ == "__main__":
    print("==================================================")
    print("    Telegram Media & Text Mirroring (Local)       ")
    print("==================================================")
    
    client.start()
    client.run_until_disconnected()
