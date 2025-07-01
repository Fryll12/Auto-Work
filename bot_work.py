import discum
import re
import time
import threading
import requests
import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# Tạo web keep_alive giữ cho bot không bị ngắt trên Render
app = Flask('')

@app.route('/')
def home():
    return "Bot Karuta đang hoạt động!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# Lấy token từ biến môi trường
tokens = os.getenv("TOKENS").split(",")

CHANNEL_ID = "1389250541590413363"
KARUTA_ID = "646937666251915264"
DELAY_BETWEEN_ACC = 10  # 10 giây giữa mỗi acc
DELAY_AFTER_ALL = 44100  # 12 tiếng 15 phút sau khi chạy hết 12 acc

def run_bot(token, acc_index):
    bot = discum.Client(token=token, log={"console": False, "file": False})

    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    step = {"value": 0}

    def send_karuta_command():
        print(f"[Acc {acc_index}] Gửi lệnh 'kc o:ef'...")
        bot.sendMessage(CHANNEL_ID, "kc o:ef")

    def send_kn_command():
        print(f"[Acc {acc_index}] Gửi lệnh 'kn'...")
        bot.sendMessage(CHANNEL_ID, "kn")

    def send_kw_command():
        print(f"[Acc {acc_index}] Gửi lệnh 'kw'...")
        bot.sendMessage(CHANNEL_ID, "kw")
        step["value"] = 2

    def click_tick(channel_id, message_id, custom_id, application_id, guild_id):
        try:
            payload = {
                "type": 3,
                "guild_id": guild_id,
                "channel_id": channel_id,
                "message_id": message_id,
                "application_id": application_id,
                "session_id": "a",
                "data": {
                    "component_type": 2,
                    "custom_id": custom_id
                }
            }
            r = requests.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
            if r.status_code == 204:
                print(f"[Acc {acc_index}] Click tick thành công!")
            else:
                print(f"[Acc {acc_index}] Click thất bại! Mã lỗi: {r.status_code}, Nội dung: {r.text}")
        except Exception as e:
            print(f"[Acc {acc_index}] Lỗi click tick: {str(e)}")

    @bot.gateway.command
    def on_message(resp):
        if resp.event.message:
            m = resp.parsed.auto()
            if str(m.get('channel_id')) != CHANNEL_ID:
                return

            author_id = str(m.get('author', {}).get('id', ''))
            guild_id = m.get('guild_id')

            if step["value"] == 0 and author_id == KARUTA_ID and 'embeds' in m and len(m['embeds']) > 0:
                desc = m['embeds'][0].get('description', '')
                card_codes = re.findall(r'\bv[a-zA-Z0-9]{6}\b', desc)
                if card_codes:
                    print(f"[Acc {acc_index}] Mã thẻ lấy được: {', '.join(card_codes[:5])}")
                    for i, code in enumerate(card_codes[:5]):
                        suffix = chr(97 + i)
                        if i == 0:
                            time.sleep(2)
                        else:
                            time.sleep(1.5)
                        bot.sendMessage(CHANNEL_ID, f"kjw {code} {suffix}")
                    time.sleep(1)
                    send_kn_command()
                    step["value"] = 1

            elif step["value"] == 1 and author_id == KARUTA_ID and 'embeds' in m and len(m['embeds']) > 0:
                desc = m['embeds'][0].get('description', '')
                lines = desc.split('\n')
                if len(lines) >= 2:
                    match = re.search(r'\d+\.\s*`([^`]+)`', lines[1])
                    if match:
                        resource = match.group(1)
                        print(f"[Acc {acc_index}] Tài nguyên chọn: {resource}")
                        time.sleep(2)
                        bot.sendMessage(CHANNEL_ID, f"kjn `{resource}` a b c d e")
                        time.sleep(1)
                        send_kw_command()

            elif step["value"] == 2 and author_id == KARUTA_ID and 'components' in m:
                message_id = m['id']
                application_id = m.get('application_id', KARUTA_ID)
                last_custom_id = None
                for comp in m['components']:
                    if comp['type'] == 1:
                        for btn in comp['components']:
                            if btn['type'] == 2:
                                last_custom_id = btn['custom_id']
                                print(f"[Acc {acc_index}] Phát hiện button, custom_id: {last_custom_id}")

                if last_custom_id:
                    click_tick(CHANNEL_ID, message_id, last_custom_id, application_id, guild_id)
                    step["value"] = 3
                    bot.gateway.close()

    print(f"[Acc {acc_index}] Bắt đầu hoạt động...")
    threading.Thread(target=bot.gateway.run, daemon=True).start()
    time.sleep(3)
    send_karuta_command()

    timeout = time.time() + 90
    while step["value"] != 3 and time.time() < timeout:
        time.sleep(1)

    bot.gateway.close()
    print(f"[Acc {acc_index}] Đã hoàn thành, chuẩn bị tới acc tiếp theo.")

def main_loop():
    while True:
        for i, token in enumerate(tokens):
            print(f"[Hệ thống] Đang chạy acc {i+1}...")
            run_bot(token, i+1)
            print(f"[Hệ thống] Acc {i+1} xong, chờ {DELAY_BETWEEN_ACC} giây...")
            time.sleep(DELAY_BETWEEN_ACC)
        
        print(f"[Hệ thống] Hoàn thành 12 acc, chờ {DELAY_AFTER_ALL} giây để lặp lại...")
        time.sleep(DELAY_AFTER_ALL)

# Khởi động web keep_alive rồi chạy bot
keep_alive()
main_loop()
