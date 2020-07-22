import netifaces
from block import BlockGenerator, LeaseManager
from configparser import ConfigParser
import struct
import socket
from dhcp import packet_base, dhcp_offer, dhcp_ack

def getType(packet):
    for option in packet.options:
        if option[0] == 53 and option[1] == 1:
            return struct.unpack('B', option[2])[0]
    return None

def getHostname(packet):
    for option in packet.options:
        if option[0] == 12:
            return struct.unpack(f'>{option[1]}s', option[2])[0]
    return None

if __name__ == '__main__':

    config = ConfigParser()
    config.read('config.txt')
    blocks = BlockGenerator(config).blocks

    lease_list = LeaseManager()

    interface_name='wlp59s0'
    port=67

    #broadcast = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['broadcast']
    try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception as e:
    	print(e)
    	exit()

    s.bind(('', port))
    while True:
        data, address = s.recvfrom(4096)
        print(f'data: {data}')
        p = packet_base(packet=data)
        p.printpacket()
        p_type = getType(p)

        ip = None
        lease = None
        block = None
        netmask = None
        router = None
        dns = None

        if p_type == 1 or p_type == 3:
            mac = p.client_mac
            hostname = getHostname(p)
            lease = LeaseManager.getLease(mac)
            if lease:
                if lease[2] < lease[1]/2:
                    lease_time = lease[1]
                else:
                    lease_time = lease[2]
                ip = lease[0]
                for block in blocks:
                    if block.name == lease[4]:
                        netmask = block.netmask
                        router = block.router
                        dns = block.dns
            else:
                for block in blocks:
                    if block.filter(hostname, mac):
                        ip = str(block.getIP())
                        lease_time = block.lease
                        netmask = block.netmask
                        router = block.router
                        dns = block.dns
            if p_type == 1:
                s_pac = dhcp_offer()
            elif p_type == 3:
                s_pac = dhcp_ack()

            s_pac.build_from_packet(data, ip, lease_time, netmask=netmask, router=router, dns=dns)
            s.sendto(s_pac.encode(), (ip, 68))
