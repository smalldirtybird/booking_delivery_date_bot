import email
import imaplib
from email.header import decode_header

from bs4 import BeautifulSoup


def get_verification_code(username, password, messages_to_chek=5):
    verification_codes = []
    imap_server = 'imap.yandex.ru'
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(username, password)
    status, messages = imap.select('INBOX')
    messages = int(messages[0])
    for i in range(messages, messages - messages_to_chek, -1):
        res, msg = imap.fetch(str(i), '(RFC822)')
        for response in msg:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding)
                if msg.is_multipart():
                    for part in msg.walk():
                        try:
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                else:
                    body = msg.get_payload(decode=True).decode()
                if subject.find('Подтверждение учетных данных Ozon') != -1:
                    soup = BeautifulSoup(body, features='html.parser')
                    soup.find_all('td')
                    code_bar = soup.find('td', attrs={
                        'height': "32",
                        'width': "124",
                    }).text
                    verification_codes.append(code_bar.replace(' ', ''))
    imap.close()
    imap.logout()
    latest, *others = verification_codes
    return latest
