from multiprocessing import Manager
from ipaddress import ip_address
import random

class UnknownBlockType(Exception):
    pass

class ConfigError(Exception):
    pass

class BlockGenerator:
    def __init__(self, config):
        l = []
        for pair in config['Blocks']:
            tar_block = config[config['Blocks'][pair]]
            type = tar_block['Assign'].lower()

            if type == 'random':
                block = RandomBlock()
            elif type == 'normal':
                block = NormalBlock()
            else:
                raise UnknownBlockType(f'Uknown block type: {type}')

            if 'Netmask' in tar_block:
                block.netmask = tar_block['Netmask']
            if 'Router' in tar_block:
                block.router = tar_block['Router']
            if 'DNS' in tar_block:
                block.dns = tarblock['DNS']
            if 'Range' in tar_block:
                if '-' in tar_block['Range']:
                    block.start_addr = ip_address(tar_block['Range'].split('-')[0])
                    block.end_addr = ip_address(tar_block['Range'].split('-')[1])
                    if not block.start_addr < block.end_addr:
                        raise ConfigError('End address is less than start address')
            block.initPool()
            l.append(block)
        self.blocks = l


class Block:
    def __init__(self):
        self.router = None
        self.start_addr = None
        self.end_addr = None
        self.netmask = None
        self.dns = None

        m = Manager()
        self.pool = m.list()

    def filter(self, hostname, mac):
        return True

    def getIP(self):
        ip = None
        try:
            ip = self.pool.pop(0)
        except Exception as e:
            print('ip pool empty')
        return ip

    def addToPool(self, item):
        self.pool.append(item)



class RandomBlock(Block):
    def __init__(self):
        super().__init__()

    def initPool(self):
        addr = self.start_addr
        while addr <= self.end_addr:
            self.pool.append(addr)
            addr += 1
        random.shuffle(self.pool)

    def addToPool(self, ip):
        self.pool.insert(random.randint(0,len(self.pool)), ip)        

class NormalBlock(Block):
    def __init__(self):
        super().__init__()

    def initPool(self):
        addr = self.start_addr
        while addr <= self.end_addr:
            self.pool.append(addr)
            addr += 1

class ListManager:
    def __init__(self, l):
        self.l = l
        # list should contain tuples of (ip, mac, lease time)

    def getLease(self, mac):
        for lease in self.l:
            if lease[1] == mac:
                return lease
        return None
