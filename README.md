# 🤖 የደሴ መረዳጃ እድር — Telegram Payment Bot

A Telegram bot that collects payment confirmations from edir members,
notifies the admin with a screenshot, and lets the admin approve or reject.

---

## 📋 Features

- ✅ Welcomes users and walks them through a step-by-step payment form
- 📸 Collects a screenshot of the bank transfer
- 🔔 Sends all info + screenshot to the admin with Approve/Reject buttons
- ✅ Notifies users of admin's decision
- 🆘 Built-in Help button showing admin's contact

---

## ⚙️ Configuration

Edit the `.env` file with your values:

```
BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_numeric_telegram_id
ADMIN_USERNAME=@YourTelegramUsername
```

> ⚠️ **Important**: The `ADMIN_USERNAME` in `.env` should be your actual
> Telegram **@username** (e.g. `@JohnDoe`). This is shown to users who need help.
> Your numeric ID (`ADMIN_CHAT_ID`) is used to send you admin notifications.

### How to get your Telegram user ID
Message [@userinfobot](https://t.me/userinfobot) on Telegram — it will reply with your numeric ID.

---

## 🚀 Deploying to Render (Free)

### Step 1 — Push to GitHub
1. Create a free account at [github.com](https://github.com)
2. Create a new repository (e.g. `payment-bot`)
3. Upload all these files to it
   > ⚠️ **Do NOT upload `.env`** — it contains your secret token!

### Step 2 — Deploy on Render
1. Go to [render.com](https://render.com) and sign up for free
2. Click **"New +"** → **"Background Worker"**
3. Connect your GitHub repository
4. Set the following:
   - **Name**: `telegram-payment-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Under **"Environment Variables"**, add:
   | Key | Value |
   |-----|-------|
   | `BOT_TOKEN` | `8714196040:AAF...` |
   | `ADMIN_CHAT_ID` | `8208198748` |
   | `ADMIN_USERNAME` | `@YourUsername` |
6. Click **"Create Background Worker"**

The bot will go live in ~2 minutes! 🎉

---

## 🧪 Running Locally (for testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

---

## 🔄 Payment Flow

```
User sends /start
  └─> Welcome + payment account info
      └─> Enter full name
          └─> Enter who they're paying for
              └─> Select group (አራዳ / ሀገር ግዛት / ሆጤ / ሳላይሽ / ሜጠሮ)
                  └─> Enter payment FROM month
                      └─> Enter payment TO month
                          └─> Send screenshot
                              └─> "Thank you! Wait up to 12 hours."
                                  └─> Admin gets notified with all info + screenshot
                                      └─> Admin clicks ✅ Approve or ❌ Reject
                                          └─> User is notified of the result
```

---

## 📁 File Structure

```
telegram-payment-bot/
├── bot.py           # Main bot logic
├── requirements.txt # Python dependencies
├── render.yaml      # Render deployment config
├── .env             # Secret keys (DO NOT commit this!)
├── .gitignore       # Excludes .env from git
└── README.md        # This file
```
