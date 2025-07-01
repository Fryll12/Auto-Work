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
    headers = {"Authorization": token, "Content-Type": "application/json"}
    step = {"value": 0}

    def send_karuta_command():
        print(f"[Acc {acc_index+1}] → Gửi lệnh 'kc o:ef'")
        bot.sendMessage(channel_id, "kc o:ef")

    def send_kn_command():
        step["value"] = 1
        print(f"[Acc {acc_index+1}] → Gửi lệnh 'kn'")
        bot.sendMessage(channel_id, "kn")

    def send_kw_command():
        step["value"] = 2
        print(f"[Acc {acc_index+1}] → Gửi lệnh 'kw'")
        bot.sendMessage(channel_id, "kw")

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

            if step["value"] == 0 and author_id == karuta_id and "embeds" in m and len(m["embeds"]) > 0:
                desc = m["embeds"][0].get("description", "")
                card_codes = re.findall(r"\bv[a-zA-Z0-9]{6}\b", desc)
                if card_codes:
                    print(f"[Acc {acc_index+1}] → Mã thẻ: {', '.join(card_codes[:5])}")
                    for i, code in enumerate(card_codes[:5]):
                        bot.sendMessage(channel_id, f"kjw {code} {chr(97 + i)}")
                        time.sleep(1.5)
                    time.sleep(1)
                    send_kn_command()

            elif step["value"] == 1 and author_id == karuta_id and "embeds" in m and len(m["embeds"]) > 0:
                desc = m["embeds"][0].get("description", "")
                lines = desc.split("\n")
                if len(lines) >= 2:
                    match = re.search(r"\d+\.\s*`([^`]+)`", lines[1])
                    if match:
                        resource = match.group(1)
                        print(f"[Acc {acc_index+1}] → Tài nguyên chọn: {resource}")
                        bot.sendMessage(channel_id, f"kjn `{resource}` a b c d e")
                        time.sleep(1)
                        send_kw_command()

            elif step["value"] == 2 and author_id == karuta_id and "components" in m:
                msg_id = m["id"]
                app_id = m.get("application_id", karuta_id)
                last_custom_id = None
                for comp in m["components"]:
                    if comp["type"] == 1:
                        for btn in comp["components"]:
                            if btn["type"] == 2:
                                last_custom_id = btn["custom_id"]
                if last_custom_id:
                    click_tick(msg_id, last_custom_id, app_id, guild_id)
                    step["value"] = 3

    bot.gateway.run()

# Hàm chạy tuần tự từng acc
def run_all():
    while True:
        for idx, token in enumerate(tokens):
            print(f"\n=== BẮT ĐẦU AUTO WORK ACC {idx+1} ===")
            auto_work(token, idx)
            print(f"=== HOÀN THÀNH ACC {idx+1}, CHỜ 2 PHÚT TIẾP THEO ===")
            time.sleep(120)
        print("\n=== HOÀN THÀNH 12 ACC, CHỜ 12 TIẾNG 15 PHÚT ===")
        time.sleep(delay_between_rounds)

keep_alive()

threading.Thread(target=run_all, daemon=True).start()

while True:
    time.sleep(60)
