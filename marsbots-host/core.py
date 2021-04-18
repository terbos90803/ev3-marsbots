import threading
import time

from bt_robot import BluetoothRobot
from tcp_robot import TcpRobot

# Robot IDs
# (number, mac, label)
#  number - Robot Number is the highly legible flag on the robot
#  mac - Mac address of the EV3's bluetooth
#  label - Sticker label on the EV3
_robot_ids = [
    {'id': 1, 'name': 'SSCI-25', 'ip': '192.168.0.125', 'btmac': '00:17:E9:B3:E3:57'},
    {'id': 2, 'name': 'SSCI-26', 'ip': '127.0.0.1', 'btmac': '00:17:E9:B3:E4:C8'},
    {'id': 3, 'name': 'SSCI-27', 'ip': '127.0.0.1', 'btmac': '00:17:E9:BA:AE:97'},
    {'id': 4, 'name': 'SSCI-29', 'ip': '127.0.0.1', 'btmac': '00:17:EC:02:E7:37'},
    {'id': 5, 'name': 'SSCI-32', 'ip': '127.0.0.1', 'btmac': '40:BD:32:3B:A6:A0'},
    {'id': 6, 'name': 'SSCI-33', 'ip': '127.0.0.1', 'btmac': '40:BD:32:3B:A3:81'}
]

# Config params
_game_minutes = 30
_game_sols = 10
_short_trip = 5
_long_trip = 20
_mins_per_sol = 1
_delay_scale = 1

# Active robots
_robots = {}

# Game timer
_game_running = False
_sol_rt_base = 0.0

# Thread safety
_lock = threading.Lock()

# Event queue
_queue = []


class _Robot:
    def __init__(self, rid):
        robot = TcpRobot(rid['ip'])
        robot.connect()
        if not robot.is_connected():
            robot = BluetoothRobot(rid['btmac'])
            robot.connect()
        self.robot = robot
        self.label = rid['name']
        self.name = None
        self.taken = False
        self.rescue = False
        self.last_ping = time.time()


def startup():
    global _robots
    for rid in _robot_ids:
        _robots[rid['id']] = _Robot(rid)


def get_game_config():
    return _game_minutes, _game_sols, _short_trip, _long_trip


def set_game_config(minutes, sols, short_trip, long_trip):
    global _game_minutes, _game_sols, _short_trip, _long_trip, _mins_per_sol, _delay_scale
    _game_minutes = minutes
    _game_sols = sols
    _short_trip = short_trip
    _long_trip = long_trip


def assign_available_robot(name):
    with _lock:
        for num, robot in _robots.items():
            if not robot.taken and robot.robot.is_connected():
                robot.taken = True
                robot.name = name
                robot.last_ping = time.time()
                return num
    return None


def get_valid_robot_numbers():
    nums = []
    for num in _robots:
        nums.append(num)
    return nums


def get_robot_label(number):
    return _robots[number].label


def get_player_name(number):
    return _robots[number].name


def start_game():
    global _sol_rt_base, _game_running, _queue, _mins_per_sol, _delay_scale
    _sol_rt_base = time.time()
    _game_running = True
    _queue = []

    _mins_per_sol = _game_minutes / _game_sols
    delay_range = _long_trip - _short_trip  # delay range in seconds
    # scale from game elapsed seconds to current light delay
    _delay_scale = float(delay_range) / float(_game_minutes * 60)


def abort_game():
    global _game_running
    _game_running = False


def is_game_running():
    return _game_running


def get_sol():
    if _game_running:
        # Update the Sol timer
        mins = (time.time() - _sol_rt_base) / 60.0
        sol_now = 1 + mins / _mins_per_sol
        return sol_now, _game_sols, _mins_per_sol
    return None


def get_light_delay():
    # Calculate the roundtrip light time from Earth to Mars
    secs = time.time() - _sol_rt_base  # game time in seconds
    return secs * _delay_scale + _short_trip


def get_connected(number):
    robot = _robots.get(number)
    return robot.robot.is_connected() if robot else False


def reconnect(number):
    robot = _robots.get(number)
    if robot:
        robot.robot.connect()


def disconnect(number):
    robot = _robots.get(number)
    if robot:
        robot.robot.close()


def get_rescue(number):
    robot = _robots.get(number)
    return robot.rescue if robot else False


def set_rescue(number):
    robot = _robots.get(number)
    if robot:
        with _lock:
            robot.rescue = True


def clear_rescue(number):
    robot = _robots.get(number)
    if robot:
        with _lock:
            robot.rescue = False


def release_robot(number):
    robot = _robots.get(number)
    if robot:
        with _lock:
            robot.taken = False


def get_taken(number):
    robot = _robots.get(number)
    if robot:
        with _lock:
            return robot.taken
    return False


def get_last_ping(number):
    robot = _robots.get(number)
    if robot:
        with _lock:
            return time.time() - robot.last_ping
    return None


def _ping(number):
    robot = _robots.get(number)
    if robot:
        with _lock:
            robot.last_ping = time.time()


def queue_plan(number, plan):
    global _queue
    _ping(number)
    if _game_running:
        delay = get_light_delay()
        due = time.time() + delay
        with _lock:
            _queue.append((due, number, plan))
        return delay
    return 0


def process_queue():
    global _queue
    if not _game_running:
        return

    now = time.time()
    q = []
    with _lock:
        while len(_queue) > 0 and _queue[0][0] <= now:
            q.append(_queue.pop(0))

    # We have quickly moved the due elements from the global queue to the local one
    # Now we can execute the plan while not holding the lock
    for e in q:
        number = e[1]
        plan = e[2]
        if plan is None:
            set_rescue(number)
        else:
            _send_plan(number, plan)


def _send_plan(number, plan):
    robot = _robots.get(number)
    if robot:
        robot.robot.send_command(plan)
