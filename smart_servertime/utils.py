
import threading
import functools

import mcdreforged.api.all as MCDR
from . import globals as GL

__all__ = [
	'new_thread', 'LockedData',
	'get_current_job', '_clear_job', 'after_job_wrapper', 'ping_job', 'after_job', 'swap_job_call', 'new_job', 'new_timer',
	'new_command', 'join_rtext', 'send_block_message', 'send_message', 'broadcast_message', 'log_info'
]

def new_thread(call):
	@MCDR.new_thread('smart_servertime')
	@functools.wraps(call)
	def c(*args, **kwargs):
		return call(*args, **kwargs)
	return c

class LockedData:
	def __init__(self, data, lock=None):
		self._data = data
		self._lock = threading.Lock() if lock is None else lock

	@property
	def d(self):
		return self._data

	@d.setter
	def d(self, data):
		self._data = data

	@property
	def l(self):
		return self._lock

	def __enter__(self):
		self._lock.__enter__()
		return self

	def __exit__(self, *args, **kwargs):
		return self._lock.__exit__(*args, **kwargs)

current_job = LockedData(None, threading.Condition(threading.RLock()))

def get_current_job():
	with current_job:
		return None if current_job.d is None else current_job.d[0]

def check_job():
	with current_job:
		return current_job.d is None

def _clear_job():
	global current_job
	current_job.d = None

def begin_job(job: str, block=False):
	global current_job
	with current_job:
		while True:
			if current_job.d is None or current_job.d is False:
				current_job.d = [job, 1]
				return True
			if not block:
				break
			current_job.l.wait()
	return False

def ping_job():
	global current_job
	with current_job:
		current_job.d[1] += 1

def after_job():
	global current_job
	with current_job:
		if current_job.d is not None:
			current_job.d[1] -= 1
			if current_job.d[1] == 0:
				current_job.d = None
				current_job.l.notify()

def after_job_wrapper(call):
	@functools.wraps(call)
	def c(*args, **kwargs):
		try:
			return call(*args, **kwargs)
		finally:
			after_job()
	return c

def swap_job_call(call, *args, **kwargs):
	global current_job
	last_job: list
	with current_job:
		assert current_job.d is not None and current_job.d is not False
		last_job, current_job.d = current_job.d, False
	try:
		return call(*args, __sst_swap_call=True, **kwargs)
	finally:
		with current_job:
			current_job.d = last_job

def new_job(job: str, block=False):
	def w(call):
		@functools.wraps(call)
		def c(*args, __sst_swap_call=False, **kwargs):
			with current_job:
				if current_job.d is not None and not __sst_swap_call and not block:
					if len(args) > 0 and isinstance(args[0], MCDR.CommandSource):
						send_message(args[0], MCDR.RText('In progress {} now'.format(current_job.d[0]), color=MCDR.RColor.red))
					else:
						log_info(MCDR.RText('In progress {0} now, cannot do {1}'.format(current_job.d[0], job), color=MCDR.RColor.red))
					return None
				begin_job(job, block=True)
			try:
				return call(*args, **kwargs)
			finally:
				after_job()
		return c
	return w

def new_timer(interval, call, args: list=None, kwargs: dict=None, daemon: bool=True, name: str='smart_servertime_timer'):
	tm = threading.Timer(interval, call, args=args, kwargs=kwargs)
	tm.name = name
	tm.daemon = daemon
	tm.start()
	return tm

def new_command(cmd: str, text=None, **kwargs):
	if text is None:
		text = cmd
	if 'color' not in kwargs:
		kwargs['color'] = MCDR.RColor.yellow
	if 'styles' not in kwargs:
		kwargs['styles'] = MCDR.RStyle.underlined
	return MCDR.RText(text, **kwargs).c(MCDR.RAction.run_command, cmd).h(cmd)

def join_rtext(*args, sep=' '):
	if len(args) == 0:
		return MCDR.RTextList()
	if len(args) == 1:
		return MCDR.RTextList(args[0])
	return MCDR.RTextList(args[0], *(MCDR.RTextList(sep, a) for a in args[1:]))

def send_block_message(source: MCDR.CommandSource, *args, sep='\n', log=False):
	if source is not None:
		t = join_rtext(GL.BIG_BLOCK_BEFOR, join_rtext(*args, sep=sep), GL.BIG_BLOCK_AFTER, sep='\n')
		source.reply(t)
		if log and source.is_player:
			source.get_server().logger.info(t)

def send_message(source: MCDR.CommandSource, *args, sep=' ', prefix=GL.MSG_ID, log=False):
	if source is not None:
		t = join_rtext(prefix, *args, sep=sep)
		source.reply(t)
		if log and source.is_player:
			source.get_server().logger.info(t)

def broadcast_message(*args, sep=' ', prefix=GL.MSG_ID):
	if GL.SERVER_INS is not None:
		GL.SERVER_INS.broadcast(join_rtext(prefix, *args, sep=sep))

def log_info(*args, sep=' ', prefix=GL.MSG_ID):
	if GL.SERVER_INS is not None:
		GL.SERVER_INS.logger.info(join_rtext(prefix, *args, sep=sep))
