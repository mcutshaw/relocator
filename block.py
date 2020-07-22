from multiprocessing import Manager
from ipaddress import ip_address
from datetime import datetime, timedelta
import random
import sys

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

            if 'Name' in tar_block:
                block.name = tar_block['name']
            if 'Netmask' in tar_block:
                block.netmask = tar_block['Netmask']
            if 'Router' in tar_block:
                block.router = tar_block['Router']
            if 'DNS' in tar_block:
                block.dns = tar_block['DNS']
            if 'Lease' in tar_block:
                block.lease = int(tar_block['Lease'])
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
        self.name = None
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

class LeaseManager:
    def __init__(self):
        m = Manager()
        self.d = m.dict()
        # list should contain tuples of (ip, mac, original lease, lease time, state, blocl_name)

    def getLease(self, mac):
        try:
            return (lease[0], lease[1], (lease[2]-datetime.now).seconds, lease[3], lease[4])
        except KeyError:
            return None

    def addLease(self,  mac, ip, original_lease, lease, state, block_name): # states: "ASSOC", "ESTB", "EXPR"
        lease = datetime.now()+timedelta(seconds=lease)
        self.d[mac] = (ip, original_lease, lease, state, block_name)
