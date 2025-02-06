
import mcdreforged.api.all as MCDR

from . import globals as glb
from .globals import *
from .utils import *
from .api import *
from .api import cooldown_timer

Prefix = '!!sst'

def register(server: MCDR.PluginServerInterface):
	cfg = get_config()
	server.register_help_message(Prefix, 'Smart Server Time help message')
	server.register_command(
		MCDR.Literal(Prefix).
		runs(command_help).
		then(cfg.literal('help').runs(command_help)).
		then(cfg.literal('wakeup').runs(command_wakeup)).
		then(cfg.literal('stop').runs(command_stop)).
		then(cfg.literal('refresh').runs(lambda src: command_refresh(src)).
			then(MCDR.Integer('timeout').at_min(0).runs(lambda src, ctx: command_refresh(src, ctx['timeout'])))).
		then(cfg.literal('reload').runs(command_config_reload)).
		then(cfg.literal('save').runs(command_config_save))
	)

def command_help(source: MCDR.CommandSource):
	send_message(source, glb.BIG_BLOCK_BEFOR, tr('help_msg', Prefix), glb.BIG_BLOCK_AFTER, sep='\n')

def command_wakeup(source: MCDR.CommandSource):
	start_server(source)

def command_stop(source: MCDR.CommandSource):
	stop_server(source)

def command_refresh(source: MCDR.CommandSource, timeout: int | None = None):
	server = source.get_server()
	if not server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already stopped, did you mean `{0} wakeup`?'.format(Prefix), color=MCDR.RColor.yellow))
		return
	if cooldown_timer is None:
		send_message(source, MCDR.RText('[WARN] Cooldown timer is not start', color=MCDR.RColor.yellow))
		return
	refresh_cooldown(timeout=timeout)
	send_message(source, tr('refresh.success'))

@new_thread
def command_config_reload(source: MCDR.CommandSource):
	get_config().load()
	send_message(source, MSG_ID, 'Config file reloaded')

@new_thread
def command_config_save(source: MCDR.CommandSource):
	get_config().save()
	send_message(source, MSG_ID, 'Config file saved')
