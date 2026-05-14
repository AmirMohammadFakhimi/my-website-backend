import os
import sys
import time
import socket
import urllib.parse
import urllib.request
from datetime import datetime

ENV_FILE = './check-educations.env'
TIMEOUT_SECONDS = 20
RETRIES = 2
RETRY_DELAY_SECONDS = 5


def load_env_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f'Missing env file: {path}')

    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('\'').strip('"')

            os.environ[key] = value


def send_telegram_message(bot_token, chat_id, message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': message,
    }).encode('utf-8')

    request = urllib.request.Request(
        url,
        data=data,
        method='POST',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )

    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        response.read()


def check_url(url):
    request = urllib.request.Request(
        url,
        method='GET',
        headers={
            'User-Agent': 'server-health-check/1.0',
        },
    )

    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        status_code = response.getcode()

        if status_code < 200 or status_code >= 400:
            raise RuntimeError(f'Bad HTTP status code: {status_code}')

        return status_code


def main():
    try:
        load_env_file(ENV_FILE)

        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        check_url_value = os.environ['CHECK_URL']

    except Exception as error:
        print(f'Config error: {error}', file=sys.stderr)
        return 2

    last_error = None

    for attempt in range(1, RETRIES + 2):
        try:
            status_code = check_url(check_url_value)
            print(f'OK: {check_url_value} returned HTTP {status_code}')
            return 0

        except Exception as error:
            last_error = error
            print(f'Attempt {attempt} failed: {error}', file=sys.stderr)

            if attempt <= RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    hostname = socket.gethostname()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    message = f'''🚨 Website check failed

URL: {check_url_value}
Server: {hostname}
Time: {now}
Error: {last_error}
'''

    try:
        send_telegram_message(bot_token, chat_id, message)
        print('Telegram alert sent.')
    except Exception as telegram_error:
        print(f'Failed to send Telegram alert: {telegram_error}', file=sys.stderr)
        return 3

    return 1


if __name__ == '__main__':
    sys.exit(main())
