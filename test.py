from block import BlockGenerator
from configparser import ConfigParser

if __name__ == '__main__':

    config = ConfigParser()
    config.read('config.txt')
    blocks = BlockGenerator(config).blocks
