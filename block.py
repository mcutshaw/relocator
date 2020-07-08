from multiprocessing import Manager

class UnknownBlockType(Exception):
    pass

class BlockGenerator(self):
    def __init__(self, config):
        l = []
        for pair in config['Blocks']:
            type = config[pair[1]]['Assign'].lower()
            if type == 'random':
                block = RandomBlock()
            elif type == 'normal':
                block = NormalBlock()
            else:
                raise UnknownBlockType(f'Uknown block type: {type}')


class Block:
    def __init__(self):
        self.start_addr = None
        self.end_addr = None
        self.netmask = None
        m = Manager()
        self.pool = m.list()

    def filter(self, hostname, mac):
        return True

    def getIP(self):
        try:
            ip = self.pool.pop()
        except:
            print('ip pool empty')


    def addToPool(self, item):
        self.pool.append(item)

class RandomBlock(Block):
    def __init__(self):
        super().__init__()
        
class NormalBlock(Block):
    def __init__(self):
        super().__init__()

class ListManager:
    def __init__(self, l):
        self.l = l
        # list should contain tuples of (ip, mac, lease time)

    def getLease(self, mac):
        for lease in self.l:
            if lease[1] == mac:
                return lease
        return None
