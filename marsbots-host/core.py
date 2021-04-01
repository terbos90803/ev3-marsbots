import threading
import time

from remote_robot import RemoteRobot


_robot_macs = [
    '00:17:E9:B3:E3:57',  # SSCI-25
    '00:17:E9:B3:E4:C8',  # SSCI-26
    '00:17:E9:BA:AE:97',  # SSCI-27
    '00:17:EC:02:E7:37',  # SSCI-29
    '40:BD:32:3B:A6:A0',  # SSCI-32
    '40:BD:32:3B:A3:81'   # SSCI-33
]

# Config params
_last_robot = 0
_game_minutes = 0
_game_sols = 0
_short_trip = 0
_long_trip = 0
_mins_per_sol = 0
_delay_scale = 0

# Active robots
_active_robots = []

# Game timer
_sol_rt_base = 0.0

# Thread safety
_lock = threading.Lock()

# Event queue
_queue = []


class _Robot:
    def __init__(self, number):
        self.robot = RemoteRobot(_robot_macs[number])
        self.robot.connect()
        self.taken = False
        self.rescue = False


def configure(number_robots, minutes, sols, short_trip, long_trip):
    global _last_robot, _game_minutes, _game_sols, _short_trip, _long_trip, _mins_per_sol, _delay_scale
    _last_robot = min(number_robots, len(_robot_macs))
    _game_minutes = minutes
    _game_sols = sols
    _short_trip = short_trip
    _long_trip = long_trip

    _mins_per_sol = _game_minutes / _game_sols
    delay_range = _long_trip - _short_trip  # delay range in seconds
    _delay_scale = float(delay_range) / float(_game_minutes * 60)  # scale from game seconds to light delay


def activate_robots():
    global _active_robots
    for ix in range(0, _last_robot):
        _active_robots.append(_Robot(ix))


def get_valid_robots():
    return 1, len(_active_robots)


def begin_game():
    global _sol_rt_base
    _sol_rt_base = time.time()


def get_sol():
    # Update the Sol timer
    mins = (time.time() - _sol_rt_base) / 60.0
    sol_now = 1 + mins / _mins_per_sol
    return sol_now, _game_sols, _mins_per_sol


def get_light_delay():
    # Calculate the roundtrip light time from Earth to Mars
    secs = time.time() - _sol_rt_base  # game time in seconds
    return secs * _delay_scale + _short_trip


def get_connected(number):
    number -= 1
    return _active_robots[number].robot.is_connected() if number < len(_active_robots) else False


def reconnect(number):
    number -= 1
    if number < len(_active_robots):
        _active_robots[number].robot.connect()


def disconnect(number):
    number -= 1
    if number < len(_active_robots):
        _active_robots[number].robot.close()


def get_rescue(number):
    number -= 1
    return _active_robots[number].rescue if number < len(_active_robots) else False


def set_rescue(number):
    number -= 1
    with _lock:
        if number < len(_active_robots):
            _active_robots[number].rescue = True


def clear_rescue(number):
    number -= 1
    with _lock:
        if number < len(_active_robots):
            _active_robots[number].rescue = False


def take_robot(number):
    number -= 1
    with _lock:
        if number < len(_active_robots):
            robot = _active_robots[number]
            if not robot.taken:
                robot.taken = True
                return True
        return False


def release_robot(number):
    number -= 1
    with _lock:
        if number < len(_active_robots):
            robot = _active_robots[number]
            robot.taken = False


def get_taken(number):
    number -= 1
    with _lock:
        if number < len(_active_robots):
            return _active_robots[number].taken
    return False


def queue_plan(number, plan):
    global _queue
    delay = get_light_delay()
    due = time.time() + delay
    with _lock:
        _queue.append((due, number, plan))
    return delay


def process_queue():
    global _queue
    now = time.time()
    q = []
    with _lock:
        while len(_queue) > 0 and _queue[0][0] <= now:
            q.append(_queue.pop(0))

    # We have quickly moved the due elements from the global queue to the local one
    for e in q:
        number = e[1]
        plan = e[2]
        if plan is None:
            set_rescue(number)
        else:
            _send_plan(number, plan)


def _send_plan(number, plan):
    number -= 1
    robot = _active_robots[number].robot
    robot.send_command(plan)
