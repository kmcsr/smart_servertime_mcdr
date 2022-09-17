
import io
import os
import json

from kpi.config import Properties

__all__ = [
	'MinecraftServer'
]

class MinecraftServer:
	def __init__(self, base: str):
		self._base = base
		self._properties = Properties(os.path.join(self._base, 'server.properties'))
		self._addr = (self._properties.get_str('server-ip', '0.0.0.0'), self._properties.get_int('server-port', 25565))
		self._modt = self._properties.get_str('motd', 'A Stopped Minecraft Server')

	@property
	def base(self):
		return self._base

	@property
	def properties(self):
		return self._properties

	@property
	def addr(self):
		return self._addr

	@property
	def modt(self):
		return self._modt

	@modt.setter
	def modt(self, modt: str):
		self._modt = modt

	def handle(self, conn, addr):
		_, pid, data = recv_package(conn)
		if pid == 0xfe:
			if conn.recv(2) == b'\x01\xfa':
				self.handle_ping_1_6(conn, addr)
			return False
		if pid == 0x00:
			prop = read_varint(data)
			host = read_string(data)
			port = int.from_bytes(data.read(2), byteorder='big')
			state = read_varint(data)
			if state == 1:
				_, pid, _ = recv_package(conn)
				if pid == 0x00:
					self.handle_ping_1_7(conn, addr)
				return False
			if state == 2:
				_, pid, data = recv_package(conn)
				if pid == 0x00:
					name = read_string(data)
					return self.handle_login(conn, addr, name)
		return False

	def handle_login(self, conn, addr, name: str):
		send_package(conn, 0x00, encode_json({
			'text': 'Server is starting, please wait a few minutes and retry'
		}))
		return True

	def handle_ping_1_7(self, conn, addr):
		res = {
			'version': {'name': 'Sleeping', 'protocol': 0},
			'players': {'max': 0, 'online': 0}
		}
		res['description'] = {
			'text': self._modt
		}
		send_package(conn, 0x00, encode_json(res))
		_, pid, data = recv_package(conn)
		if pid == 0x01:
			d = data.read(8)
			send_package(conn, 0x01, d)

	def handle_ping_1_6(self, conn, addr):
		res = '\xa71\x00'
		res += str(0) + '\x00'
		res += 'Sleeping' + '\x00'
		res += self.modt + '\x00'
		res += '0' + '\x00' + '0'
		conn.sendall(b'\xff' + len(res).to_bytes(2, byteorder='big') + res.encode('utf-16-be'))

def send_package(c, pid: int, data: bytes):
	pidb = encode_varint(pid)
	c.sendall(encode_varint(len(pidb) + len(data)))
	c.sendall(pidb)
	c.sendall(data)

def recv_package(c):
	plen, i = 0, 0
	n = recv_byte(c)
	if n == 0xfe:
		return -1, n, None
	while True:
		plen |= (n & 0x7f) << i
		if n & 0x80 == 0:
			break
		i += 7
		if i >= 32:
			raise RuntimeError('VarInt too big')
		n = recv_byte(c)
	data = b''
	while len(data) < plen:
		data += c.recv(plen - len(data))
	pr = io.BytesIO(data)
	pid = read_varint(pr)
	return plen, pid, pr

def encode_varint(n: int):
	if n == 0:
		return b'\x00'
	b = bytearray()
	while n > 0:
		x = n & 0x7f
		n >>= 7
		if n > 0:
			x |= 0x80
		b.append(x)
	return bytes(b)

def read_varint(r):
	n, i = 0, 0
	while True:
		bt = r.read(1)[0]
		n |= (bt & 0x7f) << i
		if bt & 0x80 == 0:
			break
		i += 7
		if i >= 32:
			raise RuntimeError('VarInt too big')
	return n

def encode_string(s: str):
	s = s.encode('utf8')
	return encode_varint(len(s)) + s

def encode_json(obj: dict):
	s = json.dumps(obj).encode('utf8')
	return encode_varint(len(s)) + s

def read_string(r):
	n = read_varint(r)
	s = r.read(n)
	if len(s) < n:
		raise RuntimeError('string is shorter than expected')
	return s.decode('utf8')

def recv_byte(c):
	try:
		return c.recv(1)[0]
	except IndexError:
		raise ConnectionAbortedError() from None
