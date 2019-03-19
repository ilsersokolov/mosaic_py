import logging
import os
import sys
import time

import numpy as np
# from scipy.spatial import distance
from PIL import Image
from stat import S_ISREG, ST_CTIME, ST_MODE

from config import get_config
from converter import convert_image

CONFIG_FILE = 'config.ini'
UPDATE_TIME = 15
LOG_FILE = 'mosaic.log'
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

log_formatter = logging.Formatter(FORMAT)
logger = logging.getLogger('mosaic')
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE)
fh.setFormatter(log_formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(log_formatter)
logger.addHandler(ch)


def get_option(option, section='mosaic', check=True):
    var = get_config(CONFIG_FILE, section, option)
    if not var and check:
        logger.error(f'Error: "{option}" must be initialized')
        sys.exit(1)
    return var


def make_batches(tmp_file, img_size, logo_dir, metric, worked_dir,max_h,max_w):
    h = int(max_h/img_size)
    w = int(max_w/img_size)

    im = Image.open(os.path.join(logo_dir,tmp_file)).convert('RGBA')
    im_n = im.crop((0,0,min([max_w,im.size[0]]),min([max_h,im.size[1]])))
    im = Image.new('RGBA',(max([max_w,im.size[0]]),max([max_h,im.size[1]])),(0, 0, 0, 0))
    im.paste(im_n)
    del im_n

    any_images = np.zeros((w,h),dtype=np.int)

    for i in range(h):
        for j in range(w):
            box = (img_size*j,img_size*i,img_size*(j+1),img_size*(i+1))
            part = im.crop(box)
            any_images[j,i] = np.sum(np.array(part)[:,:,3])
            alpha = np.array(part)[:,:,3]>0
            with open(os.path.join(worked_dir, str(j)+'_'+str(i)+'a.bin'), 'wb') as f:
                np.save(f, alpha)
            src = convert_image(part,metric)
            with open(os.path.join(worked_dir, str(j)+'_'+str(i)+'.bin'), 'wb') as f:
                np.save(f, src)
    with open(os.path.join(worked_dir,'parts.bin'),'wb') as f:
        np.save(f,any_images)


def get_images_bydate(worked_dir):
    dirpath = worked_dir
    # get all entries in the directory w/ stats
    entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
    entries = ((os.stat(path), path) for path in entries)

    # leave only regular files, insert creation date
    entries = ((stat[ST_CTIME], path)
            for stat, path in entries if S_ISREG(stat[ST_MODE]))
    #NOTE: on Windows `ST_CTIME` is a creation date 
    #  but on Unix it could be something else
    #NOTE: use `ST_MTIME` to sort by a modification date
    return sorted(entries,reverse=True)

def euclidean(a,b):
    return np.linalg.norm(a-b)

def mosaic(logo_dir, tmp_file, mask_file, max_h, max_w, img_size, img_dir,metric):
    worked_dir = os.path.join(logo_dir, str(img_size)+metric)
    src_dir = os.path.join(img_dir, str(img_size)+metric)
    h = int(max_h/img_size)
    w = int(max_w/img_size)
    with open(os.path.join(worked_dir,'parts.bin'),'rb') as f:
        any_images = np.load(f)
    cond = any_images==0
    any_parts = np.column_stack((np.where(cond)))
    worked_parts = np.column_stack((np.where(~cond)))
    
    images = get_images_bydate(src_dir)

    im = Image.open(os.path.join(logo_dir,tmp_file))
    mosaic = Image.new('RGBA', (max([max_w,im.size[0]]),max([max_h,im.size[1]])),(0,0,0,255))
    del im
    done_parts = []
    dic_map = {}

    dic_etalons = {}
    dic_alpha = {}
    bad_images = []
    for i in range(w):
        for j in range(h):
            filename = str(i)+'_'+str(j)
            with open(os.path.join(worked_dir,filename+'a.bin'),'rb') as f:
                dic_alpha[filename] = np.load(f)
            with open(os.path.join(worked_dir,filename+'.bin'),'rb') as f:
                dic_etalons[filename] = np.load(f)[dic_alpha[filename],:]

    for i,data in enumerate(images):
        if i >= h*w:
            break
        path = data[1]
        with open(os.path.join(src_dir+'t',os.path.basename(path)[:-4]+'.bin'),'rb') as f:
            im_src = np.load(f)
        min_dist = -1
        bst_part = ''
        if worked_parts.shape[0] <= len(done_parts):
            # TODO: fix images
            bad_images.append(os.path.basename(path)[:-4])
        else:
            for part in worked_parts:
                filename = str(part[0])+'_'+str(part[1])
                if filename in done_parts:
                    continue
                im_arr = im_src[dic_alpha[filename],:]
                # dist = distance.euclidean(np.array(dic_etalons[filename]).ravel(),np.array(im_arr).ravel())
                dist = euclidean(np.array(dic_etalons[filename]).ravel(),np.array(im_arr).ravel())
                if bst_part == '':
                    min_dist = dist
                    bst_part = filename
                else:
                    if min_dist> dist:
                        min_dist = dist
                        bst_part = filename
            dic_map[bst_part] = (os.path.basename(path)[:-4], min_dist)
            done_parts.append(bst_part)
    
    for part in any_parts:
        if len(bad_images) == 0:
            continue
        # image = bad_images.pop(np.random.choice(len(bad_images)))
        image = bad_images.pop()
        filename = str(part[0])+'_'+str(part[1])
        dic_map[filename] = (image, 0)

    black_img = Image.new('RGBA',mosaic.size, (0,0,0,0))

    for key, value in dic_map.items():
        im = Image.open(os.path.join(src_dir,value[0]+'.png'))
        i, j = key.split('_')
        i = int(i)
        j = int(j)
        box = (i*img_size,j*img_size,img_size*(i+1),img_size*(j+1))
        alpha_im = Image.new('RGBA',(img_size,img_size), (0,0,0,255))
        black_img.paste(alpha_im, box, alpha_im)
        mosaic.paste(im,box)
    
    r,g,b,a = black_img.split()
    a = a.point(lambda p: 255-p)
    black_img = Image.merge(black_img.mode, (r, g, b, a))

    mask_img = Image.open(os.path.join(logo_dir, mask_file)).convert('RGB')
    r, g, b = mask_img.getpixel((1, 1))
    mask_img_full = Image.new('RGBA',mosaic.size, (r,g,b,0))
    mask_img_full.paste(mask_img,(0,0))
    mask_img_full.putalpha(153)
    mosaic.paste(mask_img_full,(0,0),mask_img_full)
    mosaic.paste(black_img,(0,0),black_img)
    logo_img = Image.open(os.path.join(logo_dir, 'logo.png'))
    mosaic.paste(logo_img,(0,0),logo_img)
    mosaic.putalpha(255)
    mosaic.save('data/mosaic.png')


def main(logo_dir, tmp_file, mask_file, max_h, max_w, img_size, img_dir, metric):
    worked_dir = os.path.join(logo_dir, str(img_size)+metric)
    try:
        logger.info('split logo')
        os.mkdir(worked_dir)
        make_batches(tmp_file, img_size, logo_dir, metric, worked_dir,max_h,max_w)
        logger.info('done')
    except FileExistsError:
        pass

    print('Press Ctrl+C to exit')
    while True:
        try:
            logger.info('Making mosaic')
            tm = time.time()
            mosaic(logo_dir, tmp_file, mask_file, max_h, max_w, img_size, img_dir,metric)
            print(time.time()-tm)
            logger.info('Done!')
            time.sleep(UPDATE_TIME)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    logger.info('Start')
    logger.info('Reading configuration')

    logo_dir = get_option('logo dir')
    tmp_file = get_option('template file')
    mask_file = get_option('mask file')
    max_h = int(get_option('max height images'))
    max_w = int(get_option('max weight images'))

    img_size = int(get_option('image size','main'))
    img_dir = get_option('images dirrectory','main')
    metric = get_option('metric','main')

    # main(logo_dir, tmp_file, mask_file, max_h,
    #          max_w, img_size, img_dir, metric)

    try:
        main(logo_dir, tmp_file, mask_file, max_h,
             max_w, img_size, img_dir, metric)
    except Exception as ex:
        logger.error('Unknown error')
        logger.error(str(ex))
        sys.exit(1)
    logger.info('Finished!')
