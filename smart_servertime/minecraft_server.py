
import io
import os
import json

__all__ = [
	'MinecraftServer', 'Properties'
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
		send_package(conn, 0x00, encode_string(json.dumps({
			'text': 'Server is starting, please wait a few minutes and retry'
		})))
		return True

	def handle_ping_1_7(self, conn, addr):
		res = {
			'version': {'name': '0.0.0', 'protocol': 0},
			'players': {'max': 0, 'online': 0}
		}
		res['description'] = {
			'text': '[Resting]' + self._modt
		}
		send_package(conn, 0x00, encode_string(json.dumps(res)))
		_, pid, data = recv_package(conn)
		if pid == 0x01:
			d = data.read(8)
			send_package(conn, 0x01, d)

	def handle_ping_1_6(self, conn, addr):
		res = '\xa71\x00'
		res += str(0) + '\x00'
		res += '0.0.0' + '\x00'
		res += '[Resting]' + self.modt + '\x00'
		res += '0' + '\x00' + '0'
		conn.sendall(b'\xff' + len(res).to_bytes(2, byteorder='big') + res.encode('utf-16-be'))

def send_package(c, pid: int, data: bytes):
	pidb = encode_varint(pid)
	c.sendall(encode_varint(len(pidb) + len(data)))
	c.sendall(pidb)
	c.sendall(data)

def recv_package(c):
	plen = 0
	i = 0
	try:
		n = c.recv(1)[0]
	except IndexError:
		raise ConnectionAbortedError()
	if n == 0xfe:
		return -1, n, None
	while True:
		plen |= (n & 0x7f) << i
		if n & 0x80 == 0:
			break
		i += 7
		if i >= 32:
			raise RuntimeError('VarInt too big')
		n = c.recv(1)[0]
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
	n = 0
	i = 0
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

def read_string(r):
	n = read_varint(r)
	s = r.read(n)
	if len(s) < n:
		raise RuntimeError('string is too short')
	return s.decode('utf8')

class Properties:
	def __init__(self, file: str):
		self._file = file
		self._data = {}
		if os.path.exists(file):
			self.parse()

	def parse(self):
		self._data.clear()
		with open(self._file, 'r') as fd:
			for l in fd.readlines():
				l = l.strip()
				if not l or l[0] == '#':
					continue
				k, l = l.split('=')
				self._data[k] = l

	def __str__(self):
		return str(self._data)

	def __iter__(self):
		return iter(self._data)

	def __getitem__(self, key: str):
		if key not in self._data:
			raise KeyError(key)
		return self._data[key]

	def __setitem__(self, key: str, value):
		self._data[key] = str(value)

	def get(self, key: str, default=None):
		if key not in self._data:
			return default
		v = self._data[key]
		if len(v) == 0:
			return default
		return v

	def set(self, key: str, value):
		if isinstance(value, bool):
			value = 'true' if value else 'false'
		self._data[key] = str(value)

	def has(self, key: str):
		return key in self._data

	def get_int(self, key: str, default: int=0):
		return int(self.get(key, default))

	def get_float(self, key: str, default: float=0):
		return float(self.get(key, default))

	def get_str(self, key: str, default: str=''):
		return str(self.get(key, default))

	def get_bool(self, key: str, default: bool=False):
		if key not in self._data:
			return default
		return self._data[key] == 'true'
