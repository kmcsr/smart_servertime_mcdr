
import time

from .utils import *

__all__ = [
	'joined', 'left'
]

count = 0
player_count_data = []
player_log_data = {}

def joined(player: str):
	global count
	now = int(time.time())
	count += 1
	player_count_data.append((now, count))
	if player not in player_log_data:
		player_log_data[player] = [[now, None]]
	else:
		player_log_data[player].append([now, None])

def left(player: str = None):
	global count
	now = int(time.time())
	if player is None:
		count = 0
		player_count_data.append((now, 0))
		for l in player_log_data.values():
			if len(l) > 0:
				if l[-1][1] is None:
					l[-1][1] = 0
		return
	count -= 1
	player_count_data.append((now, count))
	if player in player_log_data and len(player_log_data[player]) > 0:
		if player_log_data[player][-1][1] is not None:
			log_warn(f"[SST] Player {player} seems haven't count in")
		else:
			player_log_data[player][-1][1] = now
