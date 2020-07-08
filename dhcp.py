import socket
import sys
import struct

class DecodeError(Exception):
	pass

class NotImplemented(Exception):
	pass

class packet_base:
	def __init__(self, packet = None):
		self.file_overload = False
		self.sname_overload = False

		self.message_type = 2 #1 byte (2 for boot reply, 1 for boot request)
		self.hardware_type = 1 #1 byte
		self.hardware_address_len = 6 # 1 byte
		self.hops = 0 # 1 byte
		self.transaction_id = 0 # 4 bytes will have to take from client
		self.seconds_elapsed = 0 # 2 bytes, may have to set?
		self.bootp_flags = 0 # 2 bytes, 0=unicast
		self.client_ip = 0 # 4 bytes, ip should just be set to whatever the client is asking with.
		self.your_client_ip = 0 # 4 bytes, ip I think this is what I'm offering?
		self.next_serve = 0 # 4 bytes, ip, leave blank, might be related to bootp
		self.relay_agent = 0 # 4 bytes, ip, leave blank I think related to dhcp relays
		self.client_mac = 0 # 6 bytes, mac address grab from client
		self.hardware_padding = 0 # 10 bytes, this and the above should be 16 bytes
		self.server_host_name = 0 # 64 bytes
		self.file = 0 # 128 bytes, will not be used
		self.magic_cookie = 0x63825363 # 4 bytes, needs to be set to 63 82 53 63
		self.options = [] # format for options will be (type, length, option/data), with a length of byte, byte, variable len
		# be able to receive options of at least 312 bytes, might be some weird padding to align to work boundaries

		if not packet is None:
			self.decode(packet)

	def decode(self, packet):
		self.magic_cookie = packet[236:240].hex()
		print(f'magic_cookie: {self.magic_cookie}')
		if self.magic_cookie == '63825363':
			try:
				print(f'packet length 1: {len(packet)}')
				format = '>BBBBH'
				(self.message_type,
				self.hardware_type,
				self.hardware_address_len,
				self.hops,
				self.seconds_elapsed) = struct.unpack(format, packet[:6])
				self.bootp_flags = packet[6:8].hex()
				self.client_ip = socket.inet_ntoa(packet[8:12])
				self.your_client_ip = socket.inet_ntoa(packet[12:16])
				self.next_serve = socket.inet_ntoa(packet[16:20])
				self.relay_agent = socket.inet_ntoa(packet[20:24])
				self.transaction_id = packet[24:28].hex()
				self.client_mac = packet[28:34].hex()
				self.hardware_padding = packet[34:44].hex()


				self.options = self.decodeoptions(packet[240:len(packet)])
				for option in self.options:
					if option[0] == 51:
						if option[2] == 1 or option[2] == 3:
							self.decodeoptions(packet[108:236])
							self.file_overload = True
						if option[2] == 2 or option[2] == 3:
							self.decodeoptions(packet[44:108])
							self.sname_overload = True
						break
				if not self.file_overload:
					self.file = packet[108:236]
				if not self.sname_overload:
					self.server_host_name = struct.unpack('64s', packet[44:108])[0]
			except Exception as e:
				raise DecodeError('This is not a decodeable DHCP packet')
		else:
			raise DecodeError('This is not a decodeable DHCP packet')

	def encode(self):
		data = struct.pack('>BBBBH', self.message_type,
		self.hardware_type,
		self.hardware_address_len,
		self.hops,
		self.seconds_elapsed)
		data+= bytearray.fromhex(self.bootp_flags)
		data+= socket.inet_aton(self.client_ip)
		data+= socket.inet_aton(self.your_client_ip)
		data+= socket.inet_aton(self.next_serve)
		data+= socket.inet_aton(self.relay_agent)
		data+= bytearray.fromhex(self.transaction_id)
		data+= bytearray.fromhex(self.client_mac)
		data+= bytearray.fromhex(self.hardware_padding)
		data+= self.server_host_name
		data+= self.file
		data+= self.magic_cookie
		data+= encodeoptions()

		if self.file_overload or self.sname_overload:
			raise NotImplemented('Feature not implemented')


	def encodeoptions(self):
		for option in self.options:
			data += struct.pack('>BB', option[0], option[1])
			data += option[2]
		return data

	def decodeoptions(self):
		print(f'while decoding option: {data}')
		options = []
		counter = 0
		try:
			while counter <= len(data):
				opt_type = struct.unpack('B', data[counter:counter+1])[0]
				if opt_type == 0:
					counter += 1
					continue
				counter += 1
				length = struct.unpack('B', data[counter:counter+1])[0]
				counter += 1
				opt_data = data[counter:counter+length]
				counter += length
				options.append((opt_type, length, opt_data))
		except Exception as e:
			print(e)
			print(f'something is screwy with option decoding: {data}')
		self.options += options

	def printpacket(self):
		print(f'message_type: {self.message_type}')
		print(f'hardware_type: {self.hardware_type}')
		print(f'hardware_address_len: {self.hardware_address_len}')
		print(f'hops: {self.hops}')
		print(f'transaction_id: {self.transaction_id}')
		print(f'seconds_elapsed: {self.seconds_elapsed}')
		print(f'bootp_flags: {self.bootp_flags}')
		print(f'client_ip: {self.client_ip}')
		print(f'your_client_ip: {self.your_client_ip}')
		print(f'next_serve: {self.next_serve}')
		print(f'relay_agent: {self.relay_agent}')
		print(f'client_mac: {self.client_mac}')
		print(f'hardware_padding: {self.hardware_padding}')
		print(f'server_host_name: {self.server_host_name}')
		print(f'options: {self.options}')
		print(f'file_overload: {self.file_overload}')
		print(f'sname_overload: {self.sname_overload}')
		print(f'file: {self.file}')
		print(f'magic_cookie: {self.magic_cookie}')

	def build(self, message_type, transaction_id, offering_ip, client_mac, seconds_elapsed=0,
	bootp_flags=0x0000, client_ip="0.0.0.0", next_serve="0.0.0.0",
	relay_agent="0.0.0.0", file=None, server_host_name=None, options=[],
	file_overload=False, sname_overload=False):
		self.file_overload = file_overload
		self.sname_overload = sname_overload

		self.message_type = message_type
		self.transaction_id = transaction_id # 4 bytes will have to take from client
		self.seconds_elapsed = seconds_elapsed # 2 bytes, may have to set?
		self.bootp_flags = bootp_flags # 2 bytes, 0x0000 is unicast, 0x8000 is broadcast
		self.client_ip = client_ip # 4 bytes, ip should just be set to whatever address the client talks to me with
		self.your_client_ip = offering_ip # 4 bytes, ip I think this is what I'm offering?
		self.next_serve = next_serve # 4 bytes, ip, leave blank, might be related to bootp
		self.relay_agent = relay_agent # 4 bytes, ip, leave blank I think related to dhcp relays
		self.client_mac = client_mac # 6 bytes, mac address grab from client
		self.hardware_padding = 0 # 10 bytes, this and the above should be 16 bytes
		self.server_host_name = server_host_name # 64 bytes
		self.file = file # 128 bytes, will not be used
		self.magic_cookie = 0x63825363 # 4 bytes, needs to be set to 63 82 53 63
		self.options = options # format for options will be (type, length, option/data), with a length of byte, byte, variable len
		# be able to receive options of at least 312 bytes, might be some weird padding to align to work boundaries

		main_data = self.encode()
		main_data += self.encodeoptions()

class dhcp_offer(packet_base):
	def __init__(self):
		super().__init__()

	def build_from_packet(self, packet, ip, lease_time, netmask=None, router=None, dns=None, server_ip=None):
		tar_packet = packet_base(decode=packet)
		options = []
		options.append((53, 1, struct.pack('>B', 2))) #type will be dhcp discover
		if server_ip:
			options.append((54, 4, socket.inet_aton(server_ip)))
		options.append((51, 4, struct.pack('>I',lease_time)))
		if netmask:
			options.append((1, 4, socket.inet_aton(netmask)))
		if router:
			options.append((3, 4, socket.inet_aton(router)))
		if dns:
			options.append((6, 4, socket.inet_aton(dns)))
		options.append((255, 0, b''))

		return self.build(2, tar_packet.transaction_id, ip, tar_packet.client_mac, tar_packet.seconds_elapsed, tar_packet.bootp_flags)

class dhcp_ack(packet_base):
	def __init__(self):
		super().__init__()

	def build_from_packet(self, packet, ip, lease_time, netmask=None, router=None, dns=None, server_ip=None):
		tar_packet = packet_base(decode=packet)
		options = []
		options.append((53, 1, struct.pack('>B', 5))) #type will be dhcp ack
		if server_ip:
			options.append((54, 4, socket.inet_aton(server_ip)))
		options.append((51, 4, struct.pack('>I',lease_time)))
		if netmask:
			options.append((1, 4, socket.inet_aton(netmask)))
		if router:
			options.append((3, 4, socket.inet_aton(router)))
		if dns:
			options.append((6, 4, socket.inet_aton(dns)))
		options.append((255, 0, b''))

		return self.build(2, tar_packet.transaction_id, ip, tar_packet.client_mac, tar_packet.seconds_elapsed, tar_packet.bootp_flags)
