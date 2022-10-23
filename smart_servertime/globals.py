
from typing import List, Dict, Any

import mcdreforged.api.all as MCDR

from kpi.config import Config

__all__ = [
	'MSG_ID', 'BIG_BLOCK_BEFOR', 'BIG_BLOCK_AFTER', 'SSTConfig', 'get_config', 'init', 'destory'
]

MSG_ID = MCDR.RText('[SST]', color=MCDR.RColor.light_purple)
BIG_BLOCK_BEFOR = '------------ {0} v{1} ::::'
BIG_BLOCK_AFTER = ':::: {0} v{1} ============'

class SSTConfig(Config, msg_id=MSG_ID):
	server_startup_protection: int = 10 # 10 minutes
	server_cooldown_prepare: int = 10 # 10 minutes
	# 0:guest 1:user 2:helper 3:admin 4:owner
	minimum_permission_level: Dict[str, int] = {
		'help':     0,
		'wakeup':   4,
		'stop':     3,
		'enable':   3,
		'disable':  3,
		'refresh':  3,
		'reload':   3,
		'save':     3,
	}

def get_config():
	return SSTConfig.instance()

def init(server: MCDR.PluginServerInterface):
	global BIG_BLOCK_BEFOR, BIG_BLOCK_AFTER
	metadata = server.get_self_metadata()
	BIG_BLOCK_BEFOR = BIG_BLOCK_BEFOR.format(metadata.name, metadata.version)
	BIG_BLOCK_AFTER = BIG_BLOCK_AFTER.format(metadata.name, metadata.version)
	SSTConfig.load(server.get_plugin_command_source(), server)

def destory(server: MCDR.PluginServerInterface):
	cfg = get_config()
	if cfg is not None:
		cfg.save(server.get_plugin_command_source())
