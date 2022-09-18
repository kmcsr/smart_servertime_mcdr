
import os
import threading
import socket
import traceback
import functools
from math import ceil

import mcdreforged.api.all as MCDR

from .utils import *
from . import globals as GL
from .minecraft_server import *

__all__ = [
	'ProxyServer', 'get_proxy_server'
]

def _handle_wrapper(callback):
	@functools.wraps(callback)
	def w(self, cli, addr):
		try:
			callback(self, cli, addr)
		except ConnectionAbortedError:
			pass
		except Exception as e:
			log_warn(MCDR.RText('Error when handle[{0[0]}:{0[1]}]: {1}'.format(addr, str(e)), color=MCDR.RColor.red))
			traceback.print_exc()
		finally:
			cli.close()
	return w

class ProxyServer:
	def __init__(self):
		self._lock = threading.Lock()
		self._trigger = threading.Condition(threading.Lock())
		self._trigger_call = []
		self.__status = 0
		self.__server_state = 0
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

	@_handle_wrapper
	def _handle0(self, cli, addr):
		if self._server.handle(cli, addr):
			log_info('Player [{0[0]}:{0[1]}] trying to join the game'.format(addr))
			with self._lock:
				self.__trigger()
			return True
		return False

	@MCDR.new_thread('sst_proxy_handler')
	@_handle_wrapper
	def _handle1(self, cli, addr):
		self._server.handle(cli, addr)

	@MCDR.new_thread('sst_proxy_handler')
	def _handle2(self, cli, addr):
		debug('Player [{0[0]}:{0[1]}] trying to connect'.format(addr))
		sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sok.connect(self._server.addr)
		debug('Player [{0[0]}:{0[1]}] connected the server'.format(addr))
		@MCDR.new_thread('sst_proxy_copier')
		def forward(src, dst, chunk_size: int = 1024 * 128): # chunk_size = 128KB
			try:
				while True:
					buf = src.recv(chunk_size)
					dst.sendall(buf)
			except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
				pass
			except Exception as e:
				log_warn(MCDR.RText('Error when handle[{0[0]}:{0[1]}]: {1}'.format(addr, str(e)), color=MCDR.RColor.red))
				traceback.print_exc()
			finally:
				src.close()
				dst.close()
		forward(cli, sok)
		forward(sok, cli)

	@new_thread
	def _run(self):
		with self._lock:
			self.__server_state = 0
		try:
			while self._socket is not None:
				cli, addr = self._socket.accept()
				with self._lock:
					if self.__server_state == 0:
						if self._handle0(cli, addr):
							if not GL.get_config().enable_proxy:
								break
							self.__server_state = 1
					elif self.__server_state == 1:
						if MCDR.ServerInterface.get_instance().is_server_startup():
							self._handle2(cli, addr)
						else:
							self._handle1(cli, addr)
		except ConnectionAbortedError:
			pass
		finally:
			self.stop()

	def on_server_start(self):
		with self._lock:
			if self.__server_state == 1:
				return
			self.__server_state = 1
		if not GL.get_config().enable_proxy:
			self.stop()

	def on_server_sleep(self, server: MCDR.ServerInterface):
		with self._lock:
			if self.__server_state == 0:
				return
			self.__server_state = 0
		if not GL.get_config().enable_proxy:
			self.start(server)

	def start(self, server: MCDR.ServerInterface):
		debug('Starting proxy server')
		with self._lock:
			assert not server.is_server_running()
			assert self.__status != -1, 'Proxy server is gone'
			assert self.__status != 1, 'Proxy server is already running'
			self._server = MinecraftServer(server.get_mcdr_config()['working_directory'])
			self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if GL.get_config().enable_proxy:
				self._socket.bind((GL.get_config().proxy_addr['ip'], GL.get_config().proxy_addr['port']))
			else:
				self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self._socket.bind(self._server.addr)
			self._socket.listen(ceil(self._server.max_players * 3 / 2))
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
				if final or not GL.get_config().enable_proxy:
					self._socket.close()
					self._socket = None
				self.__status = -1 if final else 0
				if not final:
					tc, self._trigger_call = self._trigger_call, []
					for c in tc:
						c()
				else:
					self._server = None
					self._trigger_call = []
				self._trigger.notify_all()

_proxy_server = ProxyServer()

def get_proxy_server():
	return _proxy_server
