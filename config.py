import configparser
import os
import sys


def create_config(filename):
    config = configparser.ConfigParser()
    config['main'] = {}
    main = config['main']
    main['hashtags'] = ''
    main['photos dirrectory'] = ''
    main['images dirrectory'] = ''
    main['metric'] = ''
    main['image size'] = ''

    config['downloader'] = {}
    downloader = config['downloader']
    downloader['app id'] = ''
    downloader['app secret'] = ''
    downloader['access token'] = ''
    downloader['business user id'] = ''

    # config['converter'] = {}
    # converter = config['converter']
    # converter[''] = ''

    config['mosaic'] = {}
    mosaic = config['mosaic']
    mosaic['max height images'] = ''
    mosaic['max weight images'] = ''
    mosaic['logo dir'] = ''
    mosaic['template file'] = ''
    mosaic['mask file'] = ''


    with open(filename, "w") as config_file:
        config.write(config_file)


def get_config(filename, section, option):
    if not os.path.exists(filename):
        create_config(filename)

    config = configparser.ConfigParser()
    config.read(filename)
    try:
        value = config.get(section, option)
    except configparser.NoOptionError as ex:
        print("Please reconfigure your config file")
        print(str(ex))
        sys.exit(1)
    return value


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("""
Usage: python config.py filename
    Create default config file
        """)
        sys.exit(1)
    create_config(sys.argv[1])
