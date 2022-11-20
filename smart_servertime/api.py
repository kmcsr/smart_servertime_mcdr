
import os
import time

import mcdreforged.api.all as MCDR

import delayexe
from loginproxy import get_proxy
from loginproxy.encoder import *
from .globals import *
from .utils import *
from . import model

__all__ = [
	'refresh_cooldown', 'stop_cooldown', 'stop_server', 'start_server'
]

cooldown_timer = LockedData(None)
server_start_time = LockedData(None)

def _timed_proxy_server():
	global cooldown_timer
	cooldown_timer.d = None
	stop_server(MCDR.ServerInterface.get_instance().get_plugin_command_source())

def refresh_cooldown(timeout: int = None):
	with cooldown_timer:
		if cooldown_timer.d is not None:
			cooldown_timer.d.cancel()
		cooldown_timer.d = new_timer((get_config().server_cooldown_prepare if timeout is None else timeout) * 60, _timed_proxy_server)

def stop_cooldown():
	global cooldown_timer
	if cooldown_timer.d is not None:
		with cooldown_timer:
			if cooldown_timer.d is not None:
				cooldown_timer.d.cancel()
				cooldown_timer.d = None

def on_load(server: MCDR.PluginServerInterface):
	global _on_login_listener
	server.register_event_listener(delayexe.ON_LAST_PLAYER_LEAVE, lambda *args: refresh_cooldown())
	cooldown_timer.d = new_timer(get_config().server_startup_protection * 60, refresh_cooldown)

	pxs = get_proxy()
	_on_login_listener = _on_login_listener0(server.get_plugin_command_source())
	pxs.on_login.append(_on_login_listener)
	pxs.on_ping.append(_on_ping_listener)

@new_thread
def on_unload(server: MCDR.PluginServerInterface):
	global cooldown_timer
	if cooldown_timer.d is not None:
		cooldown_timer.d.cancel()
		cooldown_timer.d = None

	pxs = get_proxy()
	if pxs is not None:
		pxs.on_login.remove(_on_login_listener)
		pxs.on_ping.remove(_on_ping_listener)

def on_player_joined(server: MCDR.PluginServerInterface, player: str, info: MCDR.Info):
	stop_cooldown()
	model.joined(player)

def on_player_left(server: MCDR.PluginServerInterface, player: str):
	model.left(player)

@new_thread
def on_server_start(server: MCDR.PluginServerInterface):
	now = time.time()
	with cooldown_timer:
		if cooldown_timer.d is not None:
			cooldown_timer.d.cancel()
			cooldown_timer.d = None
	with server_start_time:
		server_start_time.d = now

@new_thread
def on_server_startup(server: MCDR.PluginServerInterface):
	now = time.time()
	with cooldown_timer:
		if cooldown_timer.d is not None:
			cooldown_timer.d.cancel()
		cooldown_timer.d = new_timer(get_config().server_startup_protection * 60, refresh_cooldown)
	durt: float
	with server_start_time:
		durt = now - server_start_time.d
		server_start_time.d = None

	log_info('Server started up, used {:.02f}s'.format(durt))
	model.serevr_startup(durt)

def on_server_stop(server: MCDR.PluginServerInterface, code: int):
	stop_cooldown()

@new_thread
@job_mnr.new('proxy server')
def stop_server(source: MCDR.CommandSource):
	stop_cooldown()

	server = source.get_server()
	if not server.is_server_running():
		return
	debug('Kicking all players')
	pxs = get_proxy()
	for c in pxs.get_conns():
		c.kick()
	debug('Stopping server')
	server.stop()
	debug('Waiting server stop')
	server.wait_for_start()

@new_thread
@job_mnr.new('start server', block=True)
def start_server(source: MCDR.CommandSource):
	debug('Starting server')
	server = source.get_server()
	if server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already started', color=MCDR.RColor.yellow))
		return
	server.start()

def _on_login_listener0(source: MCDR.CommandSource):
	def cb(self, conn, addr: tuple[str, int], name: str, login_data: dict) -> bool:
		start_server(source)
		send_package(conn, 0x00, encode_json({
			'text': 'Server is starting, please wait a few minutes and retry'
		}))
		conn.close()
		return True
	return cb

_on_login_listener = None

def _on_ping_listener(self, conn, addr: tuple[str, int], login_data: dict, res: dict):
	res['players'] = {
		'max': 0,
		'online': 0,
		'sample': [
			{
				'name': 'Server stopped, please join the game to start the server',
				'id': '00000000-0000-0000-0000-000000000000'
			}
		]
	}
