
import mcdreforged.api.all as MCDR

import kpi.utils

__all__ = [
	'new_thread', 'tr'
]

kpi.utils.export_pkg(globals(), kpi.utils)

def new_thread(call):
	return MCDR.new_thread('smart_servertime')(call)

def tr(key: str, *args, **kwargs):
	return MCDR.ServerInterface.get_instance().rtr(f'smart_servertime.{key}', *args, **kwargs)
