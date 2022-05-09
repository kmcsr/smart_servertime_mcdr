
import os
import threading
import socket

import mcdreforged.api.all as MCDR
from .utils import *
from . import globals as GL

__all__ = [
	'ProxyServer', 'get_proxy_server'
]

class ProxyServer:
	def __init__(self):
		self._lock = threading.Lock()
		self._trigger = threading.Condition(threading.Lock())
		self._trigger_call = []
		self._status = 0
		self._socket = None

	@property
	def running(self):
		return self._status == 1

	@property
	def addr(self):
		if self._status != 1:
			return None, None
		return self._socket.getsockname()

	@new_thread
	def _run(self):
		self._socket.listen(1)
		try:
			while True:
				cli, addr = self._socket.accept()
				break # TODO: decode minecraft packets
		finally:
			with self._lock:
				self.__trigger()

	def start(self, server: MCDR.ServerInterface):
		assert not server.is_server_running()
		assert self._status != 1, 'Proxy server is already running'
		with self._lock:
			self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addr = _parse_serverip(server.get_mcdr_config()['working_directory'])
			self._socket.bind(addr)
			self._status = 1
		self._run()

	def stop(self):
		with self._lock:
			self.__trigger()

	def wait_trigger(self):
		with self._trigger:
			if self._status != 1:
				return
			self._trigger.wait()

	def trigger_call(self, call, immediately=True):
		with self._trigger:
			if self._status != 1:
				if immediately:
					call()
				return True
			self._trigger_call.append(call)
		return False

	def __trigger(self):
		with self._trigger:
			if self._status == 1:
				self._status = 0
				self._socket.close()
				self._socket = None
			tc, self._trigger_call = self._trigger_call, []
			for c in tc:
				c()
			self._trigger.notify_all()

_proxy_server = ProxyServer()

def get_proxy_server():
	return _proxy_server

def _parse_serverip(base: str):
	ip: str = None
	port: int = None
	with open(os.path.join(base, 'server.properties'), 'r') as fd:
		while True:
			l = fd.readline()
			if not l:
				break
			if ip is None and l.startswith('server-ip='):
				ip = l[len('server-ip='):].strip()
				if port is not None:
					break
			elif port is None and l.startswith('server-port='):
				port = int(l[len('server-port='):].strip())
				if ip is not None:
					break
	if not ip:
		ip = '0.0.0.0'
	return ip, port
