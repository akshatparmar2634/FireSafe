import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

SERVICE_ACCOUNT_FILE = 'firebase-key.json'  # path to your key file
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

project_id = credentials.project_id  # auto-detect from JSON

def get_access_token():
    credentials.refresh(Request())
    return credentials.token

def send_push_notification(fcm_token, title, body):
    access_token = get_access_token()
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8',
    }

    payload = {
        "message": {
            "token": fcm_token,
            "notification": {
                "title": title,
                "body": body
            },
            "android": {
                "priority": "high",
                "notification": {
                    "sound": "alarm",
                    "channel_id": "fire_alert_channel"
                }
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"🔔 Push response: {response.status_code} - {response.text}")
