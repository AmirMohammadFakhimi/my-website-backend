import os
import sys
import time
import socket
import urllib.parse
import urllib.request
from datetime import datetime, timedelta


ENV_FILE = './check-educations.env'
TIMEOUT_SECONDS = 20
RETRIES = 2
RETRY_DELAY_SECONDS = 5

# Runs twice a day, server local time.
CHECK_HOURS = [8, 20]


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


def run_single_check():
    load_env_file(ENV_FILE)

    bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    check_url_value = os.environ['CHECK_URL']

    last_error = None

    for attempt in range(1, RETRIES + 2):
        try:
            status_code = check_url(check_url_value)
            print(f'[{datetime.now()}] OK: {check_url_value} returned HTTP {status_code}', flush=True)
            return 0

        except Exception as error:
            last_error = error
            print(f'[{datetime.now()}] Attempt {attempt} failed: {error}', file=sys.stderr, flush=True)

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

    send_telegram_message(bot_token, chat_id, message)
    print(f'[{datetime.now()}] Telegram alert sent.', flush=True)
    return 1


def get_next_run_time():
    now = datetime.now()

    for hour in sorted(CHECK_HOURS):
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)

        if candidate > now:
            return candidate

    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=sorted(CHECK_HOURS)[0], minute=0, second=0, microsecond=0)


def run_forever():
    print(f'[{datetime.now()}] Monitor started.', flush=True)
    print(f'[{datetime.now()}] Scheduled hours: {CHECK_HOURS}', flush=True)

    while True:
        next_run = get_next_run_time()
        sleep_seconds = max(1, int((next_run - datetime.now()).total_seconds()))

        print(f'[{datetime.now()}] Next check at {next_run}', flush=True)
        time.sleep(sleep_seconds)

        try:
            run_single_check()
        except Exception as error:
            print(f'[{datetime.now()}] Unexpected monitor error: {error}', file=sys.stderr, flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        return run_single_check()

    run_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main())