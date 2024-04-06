import threading
import time
import uuid

import os

if 'MOCK_ROBOT' in os.environ and bool(os.environ['MOCK_ROBOT']):
    from mock_robot import MockRobot
    RobotClass = MockRobot
else:
    from remote_robot import RemoteRobot
    RobotClass = RemoteRobot

# Robot IDs
#  id - Robot Number is the highly legible flag on the robot
#  btmac - Mac address of the EV3's bluetooth
#  name - Sticker label on the EV3
_robot_ids = [
    {'id': 1, 'name': 'ev3dev-ssci-25', 'btmac': '00:17:E9:B3:E3:57'},
    {'id': 2, 'name': 'ev3dev-ssci-26', 'btmac': '00:17:E9:B3:E4:C8'},
    {'id': 3, 'name': 'ev3dev-ssci-27', 'btmac': '00:17:E9:BA:AE:97'},
    {'id': 4, 'name': 'ev3dev-ssci-29', 'btmac': '00:17:EC:02:E7:37'},
    {'id': 5, 'name': 'ev3dev-ssci-32', 'btmac': '40:BD:32:3B:A6:A0'},
    {'id': 6, 'name': 'ev3dev-ssci-33', 'btmac': '40:BD:32:3B:A3:81'}
]

# Config params
_game_minutes = 30
_game_sols = 10
_short_trip = 5
_long_trip = 20
_mins_per_sol = 1
_delay_scale = 1

# Active robots
_robots: 'dict[int,_Robot]' = {}

# Map users to their assigned robot
_user_robots: 'dict[_User,str]' = {}

# Game timer
_game_running = False
_game_id: str = uuid.uuid1()
_sol_rt_base = 0.0

# Thread safety
_lock = threading.Lock()

# Event queue
_queue = []


class _User:
    def __init__(self, clientId: str, name: str):
        self.clientId = clientId
        self.name = name

    def __hash__(self):
        return hash((self.clientId, self.name))

    def __eq__(self, other):
        return (self.clientId, self.name) == (other.clientId, other.name)

    def __ne__(self, other):
        return not (self == other)

class _Robot:
    def __init__(self, rid):
        self.robot = RobotClass(rid)
        self.label = rid['name']
        self.user: _User = None
        self.taken = False
        self.rescue = False
        self.last_ping = time.time()


def startup():
    global _robots
    for rid in _robot_ids:
        _robots[rid['id']] = _Robot(rid)


def shutdown():
    for r in _robots.values():
        r.robot.close()


def get_game_config():
    return _game_minutes, _game_sols, _short_trip, _long_trip


def set_game_config(minutes, sols, short_trip, long_trip):
    global _game_minutes, _game_sols, _short_trip, _long_trip, _mins_per_sol, _delay_scale
    _game_minutes = minutes
    _game_sols = sols
    _short_trip = short_trip
    _long_trip = long_trip


def found_robot(name, ip):
    with _lock:
        for rid in _robot_ids:
            if rid['name'] == name:
                _robots[rid['id']].robot.set_ip(ip)
                break

client_robot_map: 'dict[str, int]' = {
    'a57f3b90': 1,
    '573f5780': 2,
    '58f45a80': 3,
    '6d147bd0': 4,
    'e390a040': 5,
    '8cd6d300': 6
}

def get_user_robot(name: str, clientId: str):
    with _lock:
        user = _User(clientId, name)
        if user in _user_robots:
            robotId = _user_robots[user]
            _robots[robotId].last_ping = time.time()
            return robotId

        if clientId[:8] not in client_robot_map:
            return None

        robotId = client_robot_map[clientId[:8]]
        robot = _robots[robotId]

        robot.taken = True
        robot.user = user
        robot.last_ping = time.time()

        _user_robots[user] = robotId

        return robotId


def get_valid_robot_numbers():
    nums = []
    for num in _robots:
        nums.append(num)
    return nums


def get_robot_label(number):
    return _robots[number].label


def get_player_name(number):
    robot = _robots[number]
    if robot.user:
        return robot.user.name
    else:
        return None


def get_game_state():
    return (_game_running, _game_id)

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
    global _game_running, _game_id
    _game_running = False
    _game_id = uuid.uuid1()

    release_all_robots()


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


def ping_robots():
    for r in _robots.values():
        r.robot.send_command('ping')


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
            del _user_robots[robot.user]
            robot.user = None
            robot.taken = False

def release_all_robots():
    with _lock:
        rids = list(_user_robots.values())
        for rid in rids:
            robot = _robots.get(rid)
            if not robot:
                continue
            del _user_robots[robot.user]
            robot.user = None
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
