
import os
import threading
import socket
import traceback

import mcdreforged.api.all as MCDR

from .utils import *
from . import globals as GL
from .minecraft_server import *

__all__ = [
	'ProxyServer', 'get_proxy_server'
]

class ProxyServer:
	def __init__(self):
		self._lock = threading.Lock()
		self._trigger = threading.Condition(threading.Lock())
		self._trigger_call = []
		self._config = GL.get_config()
		self.__status = 0
		self._socket = None
		self._server = None

	@property
	def running(self):
		return self.__status == 1

	@property
	def finished(self):
		return self.__status == -1

	@property
	def addr(self):
		if self.__status != 1:
			return None, None
		return self._socket.getsockname()

	@new_thread
	def _run(self):
		@MCDR.new_thread('sst_proxy_handler')
		def h(cli, addr):
			try:
				if self._server.handle(cli, addr):
					log_info('Player [{0[0]}:{0[1]}] trying to join the game'.format(addr))
					with self._lock:
						self.__trigger()
			except ConnectionAbortedError:
				pass
			except BaseException as e:
				log_info(MCDR.RText('Error when handle[{0[0]}:{0[1]}]: {1}'.format(addr, str(e)), color=MCDR.RColor.red))
				traceback.print_exc()
			finally:
				cli.close()

		self._socket.listen(1)
		try:
			while True:
				cli, addr = self._socket.accept()
				h(cli, addr)
		except ConnectionAbortedError:
			pass
		finally:
			self.stop()

	def start(self, server: MCDR.ServerInterface):
		with self._lock:
			assert not server.is_server_running()
			assert self.__status != -1, 'Proxy server is gone'
			assert self.__status != 1, 'Proxy server is already running'
			self._server = MinecraftServer(server.get_mcdr_config()['working_directory'])
			self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if self._config.enable_proxy:
				self._socket.bind((self._config.proxy_addr['ip'], self._config.proxy_addr['port']))
			else:
				self._socket.bind(self._server.addr)
			self.__status = 1
		log_info('Server is proxied at {0[0]}:{0[1]}'.format(self._server.addr))
		self._run()

	def stop(self, final: bool = False):
		with self._lock:
			self.__trigger(final=final)

	def wait_trigger(self):
		with self._trigger:
			if self.__status == 1:
				self._trigger.wait()
			return self.__status == 0

	def trigger_call(self, call, immediately: bool = True):
		with self._trigger:
			if self.__status != 1:
				if immediately:
					call()
				return True
			self._trigger_call.append(call)
		return False

	def __trigger(self, final: bool = False):
		with self._trigger:
			if self.__status == 1:
				self._socket.shutdown(socket.SHUT_RDWR)
				self._socket.close()
				self.__status = -1 if final else 0
				self._socket = None
				self._server = None
				if not final:
					tc, self._trigger_call = self._trigger_call, []
					for c in tc:
						c()
				else:
					self._trigger_call = []
				self._trigger.notify_all()

_proxy_server = ProxyServer()

def get_proxy_server():
	return _proxy_server
