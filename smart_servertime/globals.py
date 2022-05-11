
from typing import List, Dict, Any

import mcdreforged.api.all as MCDR

__all__ = [
	'MSG_ID', 'BIG_BLOCK_BEFOR', 'BIG_BLOCK_AFTER', 'SSTConfig', 'Config', 'SERVER_INS', 'init', 'destory'
]

MSG_ID = MCDR.RText('[SST]', color=MCDR.RColor.green)
BIG_BLOCK_BEFOR = '------------ {0} v{1} ::::'
BIG_BLOCK_AFTER = ':::: {0} v{1} ============'

class SSTConfig(MCDR.Serializable):
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

	def literal(self, literal: str):
		lvl = self.minimum_permission_level.get(literal, 4)
		return MCDR.Literal(literal).requires(lambda src: src.has_permission(lvl),
			lambda: MCDR.RText(MSG_ID.to_plain_text() + ' 权限不足', color=MCDR.RColor.red))

	@classmethod
	def load(cls, server: MCDR.PluginServerInterface):
		global Config
		Config = server.load_config_simple(target_class=SSTConfig)

	def save(self, server: MCDR.PluginServerInterface):
		server.save_config_simple(self)


Config: SSTConfig = SSTConfig()
SERVER_INS: MCDR.PluginServerInterface = None

def init(server: MCDR.PluginServerInterface):
	global SERVER_INS
	SERVER_INS = server
	global BIG_BLOCK_BEFOR, BIG_BLOCK_AFTER
	metadata = server.get_self_metadata()
	BIG_BLOCK_BEFOR = BIG_BLOCK_BEFOR.format(metadata.name, metadata.version)
	BIG_BLOCK_AFTER = BIG_BLOCK_AFTER.format(metadata.name, metadata.version)
	SSTConfig.load(server)

def destory():
	global SERVER_INS, Config
	if Config is not None:
		Config.save(SERVER_INS)
		Config = None
	SERVER_INS = None
