# Teleclone++
A lightweight, self-hosted Python automation script built with **Telethon** to seamlessly mirror media, documents, and text from restricted or public Telegram chats directly into your Saved Messages.

TeleClone++ runs entirely locally on your machine, acting as a personal data archiver while using human-like pacing to respect Telegram's rate limits.

---

## ✨ Key Features

* **Smart Media Formatting (The MP4 Hack):** Automatically intercepts `.mkv` and other raw video documents, renames them on the fly, and injects original metadata/thumbnails to force Telegram into rendering a full-width native inline video player instead of a generic blue file box.
* **Granular Progress Tracking:** Custom visual progress bars update dynamically in a single status message to show real-time download/upload percentages, speeds, and file sizes without cluttering your chat history.
* **Anti-Ban Velocity Control:** Built-in randomized cooldown loops (8–15 seconds) between batch items mimic human behavior to shelter your account from aggressive automated spam flags.
* **Three Flexible Modes:**
* **Single Link:** Paste a solitary message link to mirror it instantly.
* **Sequential Batch:** Input a start and end link (`batch [start] [end]`) to sequentially scrape an entire range of channel history.
* **Multilink Block:** Drop a custom block of mixed text containing multiple unique links to parse and clone them all in one go.


* **Zero Cloud Dependency:** Runs completely on your local hardware—your session tokens and data never touch a third-party server.

---

## 🚀 Quick Start Guide

### 1. Prerequisites

Make sure you have Python 3.8 or higher installed on your machine. You will also need to grab your API credentials from Telegram:

1. Log into the [Telegram API Development Tools](https://my.telegram.org/).
2. Create a new application to obtain your `api_id` and `api_hash`.

### 2. Installation

Clone this repository and navigate to the project directory

### 3. Setup Configuration

Open `main.py` and replace the placeholder configuration variables at the top of the file with your actual credentials:

```python
API_ID = 12345678         # Your actual Telegram API ID
API_HASH = "your_hash_string_here"

```

### 4. Running the Script

Fire up the script from your terminal:

```bash
python main.py

```

Upon the first boot, Telethon will prompt you to enter your phone number and login code in the terminal to securely generate your local session file (`chatbot_session.session`).

---

## 📖 How To Use

Once the script prints its startup message, go to your official Telegram app, open your **Saved Messages** (`me`), and control the engine using the following commands:

| Command Structure | Description |
| --- | --- |
| `/start` | Wakes up the bot interface and prints a quick commands cheat sheet. |
| `https://t.me/c/...` | Just paste any single Telegram post link to clone its media and original caption immediately. |
| `batch [start_link] [end_link]` | Automatically scrapes and mirrors every message between the two links (inclusive). |
| `multilink [text block containing links]` | Extracts all unique links hidden within a text block and processes them one by one. |

---

## 🛡️ Safety & Rate Limits

TeleClone++ is explicitly designed to safeguard your personal Telegram account from being flagged or banned:

* **The "Saved Messages" Loophole:** Writing purely to your own cloud storage (`'me'`) skips the reporting mechanics that typical spam bots fall victim to.
* **Flood Mitigation:** If you queue a massive batch and hit a severe Telegram throttle threshold, the engine automatically catches the `FloodWaitError`, freezes the download queue, counts down safely until the restriction lifts, and seamlessly resumes work on its own.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

### Tips for customizing this on your profile:

1. **Change the repository URL** in the cloning section to point to your actual GitHub path.
2. If you eventually create a clean dark-mode UI mockup image or a quick structural diagram of how the data flows from the source channel $\rightarrow$ your laptop $\rightarrow$ Saved Messages, you can drop a clean `![Interface Preview](./preview.png)` link right underneath the main title banner!
