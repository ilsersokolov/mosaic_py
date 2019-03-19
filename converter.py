import logging
import os
import sys
import time

import numpy as np
from PIL import Image

from config import get_config

CONFIG_FILE = 'config.ini'
UPDATE_TIME = 30
LOG_FILE = 'converter.log'
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

log_formatter = logging.Formatter(FORMAT)
logger = logging.getLogger('converter')
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE)
fh.setFormatter(log_formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(log_formatter)
logger.addHandler(ch)


def get_option(option, section='main', check=True):
    var = get_config(CONFIG_FILE, section, option)
    if not var and check:
        logger.error(f'Error: "{option}" must be initialized')
        sys.exit(1)
    return var


def convert_image(image, metric):
    if metric == 'RGB':
        return np.array(image.convert('RGB'))
    if metric == 'HSV':
        return np.array(image.convert('HSV'))
    if metric == 'HUE':
        rgb = np.array(image)
        hue = np.zeros_like(rgb[..., 0])
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        sqrt3 = np.sqrt(3)
        hue = np.arctan2(sqrt3*(g-b), (2*r-g-b))
        return hue
    raise ValueError("Metrics must be in ['RGB','HSV','HUE']")


def converter(img_size, worked_dir, src_dir, metric):
    images_done = [name[:-4]
                   for name in os.listdir(worked_dir) if os.path.isfile(os.path.join(worked_dir, name))]
    photos = [name[:-4]
              for name in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, name))]

    for photo in photos:
        if photo in images_done:
            continue
        im = Image.open(os.path.join(src_dir, photo+'.jpg')).convert('RGB')
        if im.size[0] != im.size[1]:
            max_size = min(im.size)
            im_h = im.size[0]
            im_w = im.size[1]
            box = (int((im_h - max_size)/2), int((im_w - max_size)/2),
                   int((im_h + max_size)/2), int((im_w + max_size)/2))
            im = im.crop(box)
        im = im.resize((img_size, img_size))
        im.save(os.path.join(worked_dir, photo+'.png'))
        src = convert_image(im, metric)
        with open(os.path.join(worked_dir+'t', photo+'.bin'), 'wb') as f:
            np.save(f, src)
        images_done.append(photo)


def main(img_size_s, img_dir, src_dirs, metric):
    img_size = int(img_size_s)
    worked_dir = os.path.join(img_dir, img_size_s+metric)
    try:
        os.mkdir(worked_dir)
        os.mkdir(worked_dir+'t')
    except FileExistsError:
        pass
    print('Press Ctrl+C to exit')
    while True:
        try:
            logger.info('Converting photos')
            tm = time.time()
            for src_dir in src_dirs:
                logger.info(f'in dir {src_dir}')
                converter(img_size, worked_dir, src_dir, metric)
            print(time.time()-tm)
            logger.info('Done!')
            time.sleep(UPDATE_TIME)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    logger.info('Start')
    logger.info('Reading configuration')
    img_size = get_option('image size')
    img_dir = get_option('images dirrectory')
    metric = get_option('metric')
    photos_dir = get_option('photos dirrectory')
    hashtags = get_option('hashtags').lower().split(',')
    hashtags = [hashtag.strip() for hashtag in hashtags]
    src_dirs = []
    for hashtag in hashtags:
        src_dirs.append(os.path.join(photos_dir, hashtag))
    try:
        main(img_size, img_dir, src_dirs, metric)
    except Exception as ex:
        logger.error('Unknown error')
        logger.error(str(ex))
        sys.exit(1)
    logger.info('Finished!')
