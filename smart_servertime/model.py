
import time

from .utils import *

__all__ = [
	'joined', 'left', 'server_startup'
]

count = 0
player_count_data: list[tuple[int, int]] = []
player_log_data: dict = {}
server_start_durs: list[float] = []

class PlayerJoinData:
	def __init__(self, player: str, timestamp: int):
		self.player = player
		self.timestamp = timestamp

def joined(player: str):
	global count
	now = int(time.time())
	count += 1
	player_count_data.append((now, count))
	if player not in player_log_data:
		player_log_data[player] = [[now, None]]
	else:
		player_log_data[player].append([now, None])

def left(player: str | None = None):
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

def serevr_startup(durt: float) -> None:
	server_start_durs.append(durt)
	if len(server_start_durs) > 8:
		server_start_durs.pop(0)

def predict_startup_time() -> float:
	if len(server_start_durs) == 0:
		return -1
	return sum(server_start_durs) / len(server_start_durs)
