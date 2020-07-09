import netifaces
from block import BlockGenerator
from configparser import ConfigParser



if __name__ == '__main__':

    config = ConfigParser()
    config.read('config.txt')
    blocks = BlockGenerator(config).blocks

    interface_name='wlp59s0'
    port=67

    #broadcast = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['broadcast']
    try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception as e:
    	print(e)
    	sys.exit()

    s.bind(('', port))
    while True:
    	data, address = s.recvfrom(4096)
    	print(f'data: {data}')
    	p = packet_base(packet=data)
    	p.printpacket()
