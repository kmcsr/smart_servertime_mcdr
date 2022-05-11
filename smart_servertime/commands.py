
import os
import time

import mcdreforged.api.all as MCDR
from .utils import *
from . import globals as GL
from .api import *

Prefix = '!!sst'

HelpMessage = '''
{0} help :Show this help message
{0} wakeup :Start server
{0} stop :Stop server and proxy it
{0} enable :Enable this plugin
{0} disable :Disable this plugin
{0} refresh :Refresh server cooldown
{0} reload :Reload config file
{0} save :Save config file
'''.strip().format(Prefix)

def register(server: MCDR.PluginServerInterface):
	server.register_command(
		MCDR.Literal(Prefix).
		runs(command_help).
		then(GL.Config.literal('help').runs(command_help)).
		then(GL.Config.literal('wakeup').runs(command_wakeup)).
		then(GL.Config.literal('stop').runs(command_stop)).
		then(GL.Config.literal('enable').runs(command_enable)).
		then(GL.Config.literal('disable').runs(command_disable)).
		then(GL.Config.literal('refresh').runs(command_refresh)).
		then(GL.Config.literal('reload').runs(command_config_reload)).
		then(GL.Config.literal('save').runs(command_config_save))
	)

def command_help(source: MCDR.CommandSource):
	send_block_message(source, HelpMessage)

def command_wakeup(source: MCDR.CommandSource):
	start_server(source)

def command_stop(source: MCDR.CommandSource):
	server = source.get_server()
	if not server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already stopped', color=MCDR.RColor.yellow))
		return
	proxy_server(source)

def command_enable(source: MCDR.CommandSource):
	pass # TODO

def command_disable(source: MCDR.CommandSource):
	pass # TODO

def command_refresh(source: MCDR.CommandSource):
	server = source.get_server()
	if not server.is_server_running():
		send_message(source, MCDR.RText('[WARN] Server is already stopped, are you mean `{0} wakeup`?'.format(Prefix), color=MCDR.RColor.yellow))
		return
	if cooldown_timer is None:
		send_message(source, MCDR.RText('[WARN] Cooldown timer is not start', color=MCDR.RColor.yellow))
		return
	refresh_cooldown()
	send_message(source, 'Refresh successed')

@new_thread
def command_config_reload(source: MCDR.CommandSource):
	GL.SSTConfig.load(source)
	send_message(source, 'SUCCESSED reload config file')

@new_thread
def command_config_save(source: MCDR.CommandSource):
	GL.Config.save()
	send_message(source, 'Save config file SUCCESS')
