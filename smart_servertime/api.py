
import os
import time

import mcdreforged.api.all as MCDR

import loginproxy
from loginproxy.encoder import send_package, encode_json, ServerStatus
from .configs import *
from .utils import *
from . import model

__all__ = [
	'refresh_cooldown', 'stop_cooldown', 'stop_server', 'start_server'
]

cooldown_timer = None
server_start_time = None
estimate_start_dur = -1.0

def _timed_proxy_server():
	global cooldown_timer
	cooldown_timer = None
	log_warn('Countdown finished, server stopping')
	stop_server(MCDR.ServerInterface.get_instance().get_plugin_command_source())

def refresh_cooldown(timeout: int | None = None):
	global cooldown_timer
	log_info('Starting stop countdown')
	if cooldown_timer is not None:
		cooldown_timer.cancel()
	cooldown_timer = new_timer((get_config().server_cooldown_prepare if timeout is None else timeout) * 60, _timed_proxy_server)

def stop_cooldown():
	global cooldown_timer
	if cooldown_timer is not None:
		cooldown_timer.cancel()
		cooldown_timer = None
		log_info('Countdown canceled')

def on_load(server: MCDR.PluginServerInterface):
	global cooldown_timer
	server.register_event_listener(loginproxy.ON_PING, _on_ping_listener)
	server.register_event_listener(loginproxy.ON_PRE_LOGIN, _on_login_listener)
	server.register_event_listener(loginproxy.ON_LOGOFF, _on_logoff_listener)
	if loginproxy.get_proxy().get_conn_count() == 0:
		cooldown_timer = new_timer(get_config().server_startup_protection * 60, refresh_cooldown)

def on_unload(server: MCDR.PluginServerInterface):
	stop_cooldown()

def on_player_joined(server: MCDR.PluginServerInterface, player: str, info: MCDR.Info):
	stop_cooldown()
	model.joined(player)

def on_player_left(server: MCDR.PluginServerInterface, player: str):
	model.left(player)

def on_server_start(server: MCDR.PluginServerInterface):
	global server_start_time, estimate_start_dur
	now = time.time()
	stop_cooldown()
	server_start_time = now
	estimate_start_dur = model.predict_startup_time()
	log_info(f'Server starting, estimated startup time is {estimate_start_dur:.02f}s')

def on_server_startup(server: MCDR.PluginServerInterface):
	global server_start_time, cooldown_timer
	start: float
	if server_start_time is None:
		return
	start = server_start_time
	server_start_time = None

	now = time.time()
	if cooldown_timer is not None:
		cooldown_timer.cancel()
	cooldown_timer = new_timer(get_config().server_startup_protection * 60, refresh_cooldown)
	dur = now - start
	log_info(f'Server started up, used {dur:.02f}s. Estimated time was {estimate_start_dur:.02f}s')
	model.serevr_startup(dur)

def on_server_stop(server: MCDR.PluginServerInterface, code: int):
	stop_cooldown()

def stop_server(source: MCDR.CommandSource):
	stop_cooldown()

	server = source.get_server()
	if not server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already stopped', color=MCDR.RColor.yellow))
		return
	debug('Kicking all players')
	pxs = loginproxy.get_proxy()
	for c in pxs.get_conns():
		c.kick('Server stopping')
	debug('Stopping server')
	server.stop()

def start_server(source: MCDR.CommandSource):
	debug('Starting server')
	server = source.get_server()
	if server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already started', color=MCDR.RColor.yellow))
		return
	server.start()

def _on_ping_listener(server: MCDR.PluginServerInterface, proxy, conn, addr: tuple[str, int], login_data: dict, status: ServerStatus):
	if server.is_server_running():
		status.version = 'Starting'
		status.max_player = 0
		status.online_player = 0
		status.sample_players = [
			{
				'name': 'Server is starting, please wait a few minutes and retry',
				'id': '00000000-0000-0000-0000-000000000000'
			}
		]
	else:
		status.sample_players = [
			{
				'name': 'Server stopped, please join the game to start the server',
				'id': '00000000-0000-0000-0000-000000000000'
			}
		]

def _on_login_listener(server: MCDR.PluginServerInterface, proxy: loginproxy.ProxyServer, conn, addr: tuple[str, int], name: str, login_data: dict, cancel):
	if not server.is_server_running():
		start_server(server.get_plugin_command_source())
	if not server.is_server_startup():
		send_package(conn, 0x00, encode_json({
			'text': 'Server is starting, please wait a few minutes and retry\n' +
				'Estimate startup time {estimate:.2f}min'.format(estimate=estimate_start_dur / 60)
		}))
		cancel()
		return
	stop_cooldown()

def _on_logoff_listener(server: MCDR.PluginServerInterface, conn: loginproxy.Conn):
	if conn.server.get_conn_count() == 0:
		refresh_cooldown()
		return
