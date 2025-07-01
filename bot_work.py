import discum
import re
import time
import threading
import os
import requests
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

tokens = os.getenv("TOKENS").split(",")
channel_id = "1389250541590413363"
karuta_id = "646937666251915264"
delay_between_rounds = 44100  # 12 tiếng 15 phút

def auto_work(token, acc_index):
    bot = discum.Client(token=token, log=False)
    headers = {"Authorization": token}

    def send_full_work():
        print(f"[Acc {acc_index+1}] → Gửi lệnh 'kc o:ef'")
        bot.sendMessage(channel_id, "kc o:ef")
        time.sleep(8)
        bot.sendMessage(channel_id, "kn")
        time.sleep(8)
        bot.sendMessage(channel_id, "kw")
        time.sleep(8)

    def click_tick(msg_id, custom_id, app_id, guild_id):
        try:
            payload = {
                "type": 3,
                "guild_id": guild_id,
                "channel_id": channel_id,
                "message_id": msg_id,
                "application_id": app_id,
                "session_id": "a",
                "data": {"component_type": 2, "custom_id": custom_id}
            }
            r = requests.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
            if r.status_code == 204:
                print(f"[Acc {acc_index+1}] → Click tick thành công")
            else:
                print(f"[Acc {acc_index+1}] → Click tick lỗi: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"[Acc {acc_index+1}] → Lỗi click tick: {e}")

    @bot.gateway.command
    def on_message(resp):
        if resp.event.message:
            m = resp.parsed.auto()
            if str(m.get("channel_id")) != channel_id:
                return
            author_id = str(m.get("author", {}).get("id", ""))
            guild_id = m.get("guild_id")
            if author_id != karuta_id:
                return

            if "components" in m:
                msg_id = m["id"]
                app_id = m.get("application_id", karuta_id)
                for comp in m["components"]:
                    if comp["type"] == 1:
                        for btn in comp["components"]:
                            if btn["type"] == 2:
                                custom_id = btn["custom_id"]
                                click_tick(msg_id, custom_id, app_id, guild_id)
                                return

    def run_cycle():
        while True:
            send_full_work()
            time.sleep(delay_between_rounds)

    threading.Thread(target=run_cycle, daemon=True).start()
    bot.gateway.run()

keep_alive()

for idx, token in enumerate(tokens):
    threading.Thread(target=auto_work, args=(token, idx), daemon=True).start()

while True:
    time.sleep(60)
