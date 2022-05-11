
import mcdreforged.api.all as MCDR
from .utils import *
from . import globals as GL
from . import commands as CMD
from . import api

def on_load(server: MCDR.PluginServerInterface, prev_module):
	GL.init(server)
	if prev_module is None:
		log_info('Smart server time is on LOAD')
	else:
		log_info('Smart server time is on RELOAD')
		ps = prev_module.api.get_proxy_server()
		if ps.running:
			ps.stop(True)
		if not server.is_server_running():
			api.proxy_server(server.get_plugin_command_source())
	api.on_load(server)
	CMD.register(server)

def on_unload(server: MCDR.PluginServerInterface):
	log_info('Smart server time is on UNLOAD')
	api.on_unload(server)
	GL.destory()

def on_server_start(server: MCDR.PluginServerInterface):
	api.on_server_start(server)

def on_server_stop(server: MCDR.PluginServerInterface, code: int):
	api.on_server_stop(server, code)

def on_player_joined(server: MCDR.PluginServerInterface, player: str, info: MCDR.Info):
	api.on_player_joined(server, player, info)
