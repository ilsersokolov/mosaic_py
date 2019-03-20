import logging
import os
import shutil
import sys
import time

from requests import get
from requests.exceptions import ConnectionError

from config import get_config

CONFIG_FILE = 'config.ini'
UPDATE_TIME = 5*60
LOG_FILE = 'downloader.log'
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

log_formatter = logging.Formatter(FORMAT)
logger = logging.getLogger('downloader')
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE)
fh.setFormatter(log_formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(log_formatter)
logger.addHandler(ch)


def get_acces_token(app_id, app_secret):
    print("Please go to https://developers.facebook.com/tools/explorer")
    print("And get user short token")
    print('Put it here:')
    user_short_token = input()

    access_token_url = "https://graph.facebook.com/oauth/access_token?" + \
        f"grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={user_short_token}"
    try:
        r = get(access_token_url)
    except ConnectionError:
        # print('Connection error')
        logger.error('Connection error')
        sys.exit(1)
    access_token_info = r.json()
    user_long_token = access_token_info['access_token']

    print("Please insert line below to your config file as Access token\n")
    print(user_long_token)
    print('\nPress Enter to exit')
    input()
    logger.info('Successfully!')
    sys.exit(0)


def get_option(option, section='downloader', check=True):
    var = get_config(CONFIG_FILE, section, option)
    if not var and check:
        logger.error(f'Error: "{option}" must be initialized')
        sys.exit(1)
    return var


def get_hashtag_id(user_id, hashtag, access_token):
    logger.info('Get hashtag ID')
    answer = get(f'https://graph.facebook.com/ig_hashtag_search?user_id={user_id}&q={hashtag}&access_token={access_token}',
                 verify=True).json()
    try:
        hashtag_id = answer['data'][0]['id']
    except KeyError:
        logger.info('Failed!')
        sys.exit(1)
    logger.info('Successfully!')
    return hashtag_id


def load_photos(worked_dir, url):
    photos_done = [name for name in os.listdir(worked_dir)
                   if os.path.isfile(os.path.join(worked_dir, name))]
    work = True
    while work:
        try:
            response = get(url, verify=True)
        except ConnectionError:
            logger.error('Connection error')
            logger.info(f'waiting {UPDATE_TIME} s')
            time.sleep(UPDATE_TIME)
            logger.info('Exit with sys 1')
            sys.exit(1)
        answer = response.json()
        try:
            data = answer['data']
        except KeyError:
            logger.info('all photoes at last 24 hours downloaded')
            break

        for dt in data:
            filename = dt['id']+'.jpg'
            if dt['media_type'] == 'IMAGE':
                if filename in photos_done:
                    work = False
                    break
                response = get(dt['media_url'], stream=True)
                with open(os.path.join(worked_dir, filename), 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response
                photos_done.append(filename)
        try:
            url = answer['paging']['next']
        except KeyError:
            work = False
            logger.info('all photoes at last 24 hours downloaded')


def main(hashtags, photos_dir, user_id, access_token):
    worked_dirs = {}
    urls = {}
    for hashtag in hashtags:
        worked_dirs[hashtag] = os.path.join(photos_dir, hashtag)
        hashtag_id = get_hashtag_id(user_id, hashtag, access_token)
        urls[hashtag] = f'https://graph.facebook.com/{hashtag_id}/recent_media?user_id={user_id}&limit=50&fields=id,media_url,permalink,media_type&access_token={access_token}'
        try:
            os.mkdir(worked_dirs[hashtag])
        except FileExistsError:
            pass
    print('Press Ctrl+C to exit')
    while True:
        try:
            logger.info('Download photos')
            for hashtag in hashtags:
                logger.info(f'for #{hashtag.upper()}')
                load_photos(worked_dirs[hashtag], urls[hashtag])
            logger.info('Done!')
            time.sleep(UPDATE_TIME)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    logger.info('Start')
    logger.info('Reading configuration')
    hashtags = get_option('hashtags','main').lower().split(',')
    hashtags = [hashtag.strip() for hashtag in hashtags]
    photos_dir = get_option('photos dirrectory','main')
    user_id = get_option('business user id')

    access_token = get_option('access token', check=False)
    if not access_token:
        logger.info('Get Access token')
        app_id = get_option('app id')
        app_secret = get_option('app secret')
        get_acces_token(app_id, app_secret)

    # main(hashtags, photos_dir, user_id, access_token)

    try:
        main(hashtags, photos_dir, user_id, access_token)
    except Exception as ex:
        logger.error('Unknown error')
        logger.error(str(ex))
        sys.exit(1)

    logger.info('Finished!')
