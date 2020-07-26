import netifaces
from block import BlockGenerator, LeaseManager
from configparser import ConfigParser
import struct
import socket
from dhcp import packet_base, dhcp_offer, dhcp_ack, dhcp_nack
import multiprocessing
import time


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

def serve(config, blocks, lease_list):



    interface_name='wlp59s0'
    port=67

    #broadcast = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['broadcast']
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        #s.setsockopt(socket.SOL_SOCKET, 25, str("ens33" + '\0').encode('utf-8'))
    except Exception as e:
    	print(e)
    	exit()
    s.bind(('255.255.255.255', port))
    while True:
        data, address = s.recvfrom(4096)
        #print(f'data: {data}')
        p = packet_base(packet=data)
        #p.printpacket()
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
            lease = lease_list.getLease(mac)
            if lease:
                lease_list.setID(mac, p.transaction_id)
                if lease[2] < lease[1]/2:
                    lease_time = lease[1]
                    lease_list.resetLease(mac)
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
                        lease_list.addLease(mac, ip, lease_time, lease_time, 'ASSOC', block.name, p.transaction_id)
            if p_type == 1:
                s_pac = dhcp_offer()
            elif p_type == 3:
                s_pac = dhcp_ack()
            s_pac.build_from_packet(data, ip, lease_time, netmask=netmask, router=router, dns=dns)
            print(f'offering ip {s_pac.your_client_ip}')
            s.sendto(s_pac.encode(), ('255.255.255.255', 68))

if __name__ == '__main__':
    config_name = 'config.txt'
    config = ConfigParser()
    config.read(config_name)

    blocks = BlockGenerator(config).blocks

    lease_list = LeaseManager()

    p = multiprocessing.Process(target=serve, args=(config, blocks, lease_list))
    p.start()
    p.join()
