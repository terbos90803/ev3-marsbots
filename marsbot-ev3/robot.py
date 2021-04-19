#!/usr/bin/env python3
"""
SSCI SoccerBot robot server
"""

import remote
import pickle
import json
import time

from ev3dev2 import DeviceNotFound
from ev3dev2.motor import MediumMotor, MoveSteering, SpeedPercent, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.led import Led, Leds
from ev3dev2.display import Display
from Screen import init_console, reset_console, debug_print


FORWARD = u'\u2191' # up-arrow glyph
REVERSE = u'\u2193' # down-arrow glyph
LEFT = u'\u2190' # left-arrow glyph
RIGHT = u'\u2192' # right-arrow glyph
GRAB = 'Grab'
RELEASE = 'Release'

driveSpeed = 35
turnSpeed = 35
grabSpeed = 40
holdSpeed = 10

init_console()

# get handles for the three motors
grabMotor = None
steeringDrive = None
while True:
    try:
        grabMotor = grabMotor if grabMotor else MediumMotor(OUTPUT_A)
        steeringDrive = steeringDrive if steeringDrive else MoveSteering(OUTPUT_B, OUTPUT_C)
        break
    except DeviceNotFound as error:
        print("Motor not connected")
        print("Check and restart")
        print(error)
        time.sleep(1)

debug_print('stop actions:', grabMotor.stop_actions)
debug_print('pickle.HIGHEST_PROTOCOL:', pickle.HIGHEST_PROTOCOL)


def move(value):
    steeringDrive.on_for_rotations(0, driveSpeed, 1.0 * value)


def turn(value):
    steering = -100 if value < 0 else 100
    steeringDrive.on_for_rotations(steering, turnSpeed, 0.4925 * value)


def grab():
    grabMotor.duty_cycle_sp = -grabSpeed
    grabMotor.run_direct()
    time.sleep(0.1)
    grabMotor.wait_until_not_moving()
    grabMotor.duty_cycle_sp = -holdSpeed


def release():
    grabMotor.stop_action = 'coast'
    grabMotor.duty_cycle_sp = grabSpeed
    grabMotor.run_direct()
    time.sleep(0.1)
    grabMotor.wait_until_not_moving()
    grabMotor.stop()


leds = Leds()
#debug_print(Led().triggers)
leds.set('LEFT', trigger='default-on')
leds.set('RIGHT', trigger='default-on')

display = Display()
screenw = display.xres
screenh = display.yres

# reset the grab motor to a known good position
release()

# Create connection to server
s, host_address = remote.get_listener_socket()
s.settimeout(5)

# Main loop handles connections to the host
while True:
    try:
        reset_console()
        print (host_address)
        leds.set_color('LEFT', 'AMBER')
        leds.set_color('RIGHT', 'AMBER')
        debug_print('Waiting for connection')
        remote.advertise()

        try:
            client, clientInfo = s.accept()
        except:
            continue

        client.settimeout(10)
        print ('Connected')
        debug_print('Connected to:', clientInfo)
        leds.set_color('LEFT', 'GREEN')
        leds.set_color('RIGHT', 'GREEN')

        # Driving loop
        while True:
            data = client.recv(remote.size)
            #debug_print('recv:', data)
            if data == b'':
                client.close()
                break

            if data:
                #debug_print(data)
                jd = pickle.loads(data)
                #debug_print(jd)
                if jd == 'ping':
                    continue

                sequence = json.loads(jd)

                # command format: [[cmd, value], ...]
                #debug_print(sequence)
                if isinstance(sequence, list):
                    for step in sequence:
                        #debug_print(step)
                        cmd = step[0]
                        #debug_print(cmd)
                        value = float(step[1]) if len(step) > 1 else 0.0
                        #debug_print(value)
                        if cmd == FORWARD:
                            move(value)
                        elif cmd == REVERSE:
                            move(-value)
                        elif cmd == LEFT:
                            turn(-value)
                        elif cmd == RIGHT:
                            turn(value)
                        elif cmd == GRAB:
                            grab()
                        elif cmd == RELEASE:
                            release()
    except:
        client.close()
s.close()
