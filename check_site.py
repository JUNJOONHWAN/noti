import requests
import json
import os
from datetime import datetime, timedelta

URL = "http://54.66.22.155:7860"  # 체크할 사이트
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # GitHub Secret에서 불러옴
ALERT_FILE = "last_alert.txt"
FAIL_COUNT_FILE = "fail_count.txt"
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

def get_fail_count():
    if os.path.exists(FAIL_COUNT_FILE):
        with open(FAIL_COUNT_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

def update_fail_count(count):
    with open(FAIL_COUNT_FILE, "w") as f:
        f.write(str(count))

def check_website():
    try:
        response = requests.get(URL, timeout=10)
        if response.status_code == 200:
            print(f"[OK] {URL} 정상 동작")
            update_fail_count(0)  # 정상 시 실패 카운트 초기화
            return
        else:
            handle_failure(f"⚠️ {URL} 응답 이상 (status: {response.status_code})")
    except requests.RequestException:
        handle_failure(f"🚨 {URL} 접속 불가!")

def handle_failure(message):
    fail_count = get_fail_count()
    fail_count += 1
    update_fail_count(fail_count)

    if fail_count >= 2:  # 연속 2회 실패 시
        last_alert = get_last_alert_time()
        now = datetime.utcnow()
        if last_alert is None or (now - last_alert) > timedelta(seconds=ALERT_INTERVAL):
            send_slack_alert(message)
            update_last_alert_time()
        else:
            print("알림 보류 (최근 1시간 내 이미 전송됨)")
    else:
        print(f"첫 번째 실패 감지 (연속 실패 카운트: {fail_count}) → 알림 없음")

if __name__ == "__main__":
    check_website()
