import requests
import json
import os
import time
from datetime import datetime, timedelta

URL = "http://54.66.22.155:7860"  # 체크할 사이트
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # GitHub Secret에서 불러옴
ALERT_FILE = "last_alert.txt"
ALERT_INTERVAL = 3600  # 1시간(초)

def send_slack_alert(message):
    payload = {"text": message}
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))

def get_last_alert_time():
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            ts = f.read().strip()
            try:
                return datetime.fromisoformat(ts)
            except:
                return None
    return None

def update_last_alert_time():
    with open(ALERT_FILE, "w") as f:
        f.write(datetime.utcnow().isoformat())

def check_once():
    try:
        response = requests.get(URL, timeout=10)
        if response.status_code == 200:
            print(f"[OK] {URL} 정상 동작")
            return True
        else:
            print(f"[WARN] {URL} 응답 이상 (status: {response.status_code})")
            return False
    except requests.RequestException:
        print(f"[FAIL] {URL} 접속 불가!")
        return False

def check_website():
    # 첫 번째 시도
    if check_once():
        return

    # 첫 번째 실패 → 5분 대기 후 재시도
    print("⏳ 5분 대기 후 재시도...")
    time.sleep(300)

    if not check_once():
        # 두 번째도 실패하면 알림
        last_alert = get_last_alert_time()
        now = datetime.utcnow()
        if last_alert is None or (now - last_alert) > timedelta(seconds=ALERT_INTERVAL):
            send_slack_alert(f"🚨 {URL} 접속 불가 또는 응답 이상!")
            update_last_alert_time()
        else:
            print("알림 보류 (최근 1시간 내 이미 전송됨)")

if __name__ == "__main__":
    check_website()
