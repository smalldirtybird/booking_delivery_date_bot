import os
import pickle

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://mail.google.com/']


def gmail_authenticate(credentials):
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = []
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(
            userId='me',
            q=query,
            pageToken=page_token,
        ).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages


def read_message(service, message):
    msg = service.users().messages().get(
        userId='me',
        id=message['id'],
        format='full',
    ).execute()
    return msg['internalDate'], msg['snippet']


def get_verification_code(credentials):
    load_dotenv()
    service = gmail_authenticate(credentials)
    messages = search_messages(service, 'Подтверждение учетных данных Ozon')
    newest_code = {}
    for message in messages:
        timestamp, snippet = read_message(service, message)
        if not newest_code or timestamp >= newest_code['timestamp']:
            newest_code['timestamp'] = timestamp
            newest_code['code'] = snippet[112:118]
    return newest_code['code']
