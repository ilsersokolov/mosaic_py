import os

from config import create_config

try:
    os.mkdir('data')
except FileExistsError:
    pass

try:
    os.mkdir('data/images')
except FileExistsError:
    pass

try:
    os.mkdir('data/logo')
except FileExistsError:
    pass

try:
    os.mkdir('data/photos')
except FileExistsError:
    pass

create_config('Default.cfg')
