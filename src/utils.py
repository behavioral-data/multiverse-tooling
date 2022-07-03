import logging
from os.path import dirname, abspath, join

PROJECT_ROOT_DIR = dirname(dirname(abspath(__file__)))
DATA_DIR = join(PROJECT_ROOT_DIR, 'data')
SRC_DIR = join(PROJECT_ROOT_DIR, 'src')

def get_logger(name):
    logger = logging.getLogger(name)
    logging.basicConfig(
        forloggmat="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO
    )
    return logger

if __name__ == '__main__':
    print(PROJECT_ROOT_DIR)