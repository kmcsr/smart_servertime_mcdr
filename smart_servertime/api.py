
import os
import time

import mcdreforged.api.all as MCDR

import delayexe
from . import globals as GL
from .utils import *
from .proxy_server import *

__all__ = [
	'get_proxy_server', 'refresh_cooldown', 'stop_cooldown', 'proxy_server', 'start_server'
]

cooldown_timer = LockedData(None)

def _timed_proxy_server():
	global cooldown_timer
	cooldown_timer.d = None
	proxy_server(MCDR.ServerInterface.get_instance().get_plugin_command_source())

def refresh_cooldown(timeout: int = None):
	with cooldown_timer:
		if cooldown_timer.d is not None:
			cooldown_timer.d.cancel()
		cooldown_timer.d = new_timer((GL.get_config().server_cooldown_prepare if timeout is None else timeout) * 60, _timed_proxy_server)

def stop_cooldown():
	global cooldown_timer
	if cooldown_timer.d is not None:
		with cooldown_timer:
			if cooldown_timer.d is not None:
				cooldown_timer.d.cancel()
				cooldown_timer.d = None

def on_load(server: MCDR.PluginServerInterface):
	server.register_event_listener(delayexe.ON_PLAYER_EMPTY, lambda *args: refresh_cooldown())
	# if not server.is_server_running():
	# 	proxy_server(server.get_plugin_command_source())
	# else:
	cooldown_timer.d = new_timer(GL.get_config().server_startup_protection * 60, refresh_cooldown)

@new_thread
def on_unload(server: MCDR.PluginServerInterface):
	global cooldown_timer
	if cooldown_timer.d is not None:
		cooldown_timer.d.cancel()
		cooldown_timer.d = None
	get_proxy_server().stop(True)

def on_player_joined(server: MCDR.PluginServerInterface, player: str, info: MCDR.Info):
	stop_cooldown()

@new_thread
def on_server_start(server: MCDR.PluginServerInterface):
	if get_proxy_server().running:
		get_proxy_server().stop()
	with cooldown_timer:
		if cooldown_timer.d is not None:
			cooldown_timer.d.cancel()
		cooldown_timer.d = new_timer(GL.get_config().server_startup_protection * 60, refresh_cooldown)

def on_server_stop(server: MCDR.PluginServerInterface, code: int):
	stop_cooldown()

@new_thread
@job_mnr.new('proxy server')
def proxy_server(source: MCDR.CommandSource):
	stop_cooldown()

	server = source.get_server()
	if server.is_server_running():
		server.stop()
		server.wait_for_start()
	pxs = get_proxy_server()
	pxs.start(server)
	pxs.trigger_call(lambda: start_server(server.get_plugin_command_source()))

@new_thread
@job_mnr.new('start server', block=True)
def start_server(source: MCDR.CommandSource):
	server = source.get_server()
	if server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already started', color=MCDR.RColor.yellow))
		return
	get_proxy_server().stop()
	server.start()
