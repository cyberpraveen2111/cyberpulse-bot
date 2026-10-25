import os
import requests

TOKEN = "8964911496:AAGDFmg-2BhUg16Db3zfFZrKCrFsLWM6DAw"
USERS_FILE = "users.txt"

try:
  # 1. Fetch incoming messages from Telegram
  res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()

  existing_users = set()
  if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
      existing_users.update(f.read().splitlines())

  updated_users = set(existing_users)

  # 2. Check for new users and send instant welcome message
  if res.get("ok"):
    for update in res.get("result", []):
      chat = update.get("message", {}).get("chat", {})
      chat_id = str(chat.get("id"))

      if chat_id and chat_id != "None":
        if chat_id not in existing_users:
          welcome_msg = (
              "Your ID has been recorded! You will now regularly get cybernews"
              " on time - 08:48 PM IST."
          )
          requests.post(
              f"https://api.telegram.org/bot{TOKEN}/sendMessage",
              json={"chat_id": chat_id, "text": welcome_msg},
          )
          print(f"Welcomed new user: {chat_id}")

        updated_users.add(chat_id)

  # Save updated user list locally
  with open(USERS_FILE, "w") as f:
    f.write("\n".join(updated_users))

  # 3. Fetch latest cybersecurity news for broadcast
  news_res = requests.get(
      "https://api.rss2json.com/v1/api.json?rss_url=https://feeds.feedburner.com/TheHackersNews"
  ).json()
  items = news_res.get("items", [])[:5]

  msg = "🛡️ *CYBERPULSE DAILY THREAT BRIEFING*\n━━━━━━━━━━━━━━━━━━━━\n"
  for idx, item in enumerate(items, 1):
    msg += f"\n*{idx}. {item.get('title')}*\n🔗 {item.get('link')}\n"

  # 4. Broadcast news to all registered users
  for cid in updated_users:
    if cid.strip():
      requests.post(
          f"https://api.telegram.org/bot{TOKEN}/sendMessage",
          json={"chat_id": cid.strip(), "text": msg, "parse_mode": "Markdown"},
      )

  print(f"Broadcasted news to {len(updated_users)} users successfully!")
except Exception as e:
  print(f"Error: {e}")
