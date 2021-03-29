from remote_robot import RemoteRobot
from command import Command


robot_macs = [
    '00:17:E9:B3:E3:57',  # SSCI-25
    '00:17:E9:B3:E3:57',  # SSCI-26
    '00:17:E9:B3:E3:57',  # SSCI-27
    '00:17:E9:B3:E3:57',  # SSCI-29
    '00:17:E9:B3:E3:57',  # SSCI-32
    '00:17:E9:B3:E3:57'   # SSCI-33
]

# Config params
_last_robot = 0
_game_minutes = 0
_game_sols = 0
_short_trip = 0
_long_trip = 0

# Active robots
_active_robots = []


def configure(number_robots, minutes, sols, short_trip, long_trip):
    global _last_robot, _game_minutes, _game_sols, _short_trip, _long_trip
    _last_robot = min(number_robots, len(robot_macs))
    _game_minutes = minutes
    _game_sols = sols
    _short_trip = short_trip
    _long_trip = long_trip


def activate_robots():
    global _active_robots
    for ix in range(0, _last_robot):
        robot = RemoteRobot(robot_macs[ix])
        robot.connect()
        _active_robots.append(robot)


def get_valid_robots():
    return 1, len(_active_robots)

