import os
import threading
import time
from flask import Flask
import requests
import schedule

TOKEN = "8964911496:AAGDFmg-2BhUg16Db3zfFZrKCrFsLWM6DAw"
USERS_FILE = "users.txt"

# Simple Flask app to satisfy Render's web service requirement
app = Flask(__name__)


@app.route("/")
def home():
  return "CyberPulse Bot is active!"


def load_users():
  if os.path.exists(USERS_FILE):
    try:
      with open(USERS_FILE, "r") as f:
        return set(f.read().splitlines())
    except Exception:
      pass
  return set()


def save_users(users):
  try:
    with open(USERS_FILE, "w") as f:
      f.write("\n".join(users))
  except Exception as e:
    print(f"Error saving users: {e}")


def send_daily_news():
  try:
    users = load_users()
    if not users:
      return

    news_res = requests.get(
        "https://api.rss2json.com/v1/api.json?rss_url=https://feeds.feedburner.com/TheHackersNews",
        timeout=10,
    )
    if news_res.status_code != 200 or not news_res.text.strip():
      return
    news_data = news_res.json()
    items = news_data.get("items", [])[:5]

    msg = "🛡️ *CYBERPULSE DAILY THREAT BRIEFING*\n━━━━━━━━━━━━━━━━━━━━\n"
    for idx, item in enumerate(items, 1):
      msg += f"\n*{idx}. {item.get('title')}*\n🔗 {item.get('link')}\n"

    for cid in users:
      if cid.strip():
        try:
          requests.post(
              f"https://api.telegram.org/bot{TOKEN}/sendMessage",
              json={"chat_id": cid.strip(), "text": msg, "parse_mode": "Markdown"},
              timeout=10,
          )
        except Exception:
          pass
    print(f"Daily news broadcasted to {len(users)} users successfully!")
  except Exception as e:
    print(f"Broadcast error: {e}")


def run_bot():
  # Schedule daily news at 9:35 PM IST (16:05 UTC)
  schedule.every().day.at("16:05").do(send_daily_news)
  print("CyberPulse Bot background worker started...")

  offset = 0
  while True:
    try:
      res = requests.get(
          f"https://api.telegram.org/bot{TOKEN}/getUpdates",
          params={"offset": offset, "timeout": 30},
          timeout=35,
      )

      if res.status_code == 200 and res.text.strip():
        data = res.json()
        if data.get("ok"):
          for update in data.get("result", []):
            offset = update["update_id"] + 1
            chat = update.get("message", {}).get("chat", {})
            chat_id = str(chat.get("id"))

            if chat_id and chat_id != "None":
              users = load_users()
              if chat_id not in users:
                users.add(chat_id)
                save_users(users)
                welcome_msg = (
                    "Your ID has been recorded! You will now regularly get"
                    " cybernews on time - 09:35 PM IST."
                )
                try:
                  requests.post(
                      f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      json={"chat_id": chat_id, "text": welcome_msg},
                      timeout=10,
                  )
                except Exception:
                  pass

      schedule.run_pending()
    except Exception as e:
      print(f"Polling warning: {e}")
      time.sleep(5)


if __name__ == "__main__":
  # Start the Telegram bot loop in a background thread
  t = threading.Thread(target=run_bot)
  t.daemon = True
  t.start()

  # Run Flask server on Render's assigned port
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
