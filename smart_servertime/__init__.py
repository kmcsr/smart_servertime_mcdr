
import mcdreforged.api.all as MCDR

from . import configs
from .utils import *
from . import commands as CMD
from . import api

def on_load(server: MCDR.PluginServerInterface, prev_module):
	if prev_module is None:
		log_info('Smart server time is on LOAD')
	else:
		log_info('Smart server time is on RELOAD')
	configs.init(server)
	api.on_load(server)
	CMD.register(server)

def on_unload(server: MCDR.PluginServerInterface):
	log_info('Smart server time is on UNLOAD')
	api.on_unload(server)
	configs.destory(server)

def on_server_start(server: MCDR.PluginServerInterface):
	api.on_server_start(server)

def on_server_startup(server: MCDR.PluginServerInterface):
	api.on_server_startup(server)

def on_server_stop(server: MCDR.PluginServerInterface, code: int):
	api.on_server_stop(server, code)

def on_player_joined(server: MCDR.PluginServerInterface, player: str, info: MCDR.Info):
	api.on_player_joined(server, player, info)

def on_player_left(server: MCDR.PluginServerInterface, player: str):
	api.on_player_left(server, player)
