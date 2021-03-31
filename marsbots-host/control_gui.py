import PySimpleGUI as sg
import core
import get_public_ip

_how_many_robots_key = '-HOW-MANY-ROBOTS-'
_how_many_minutes_key = '-HOW-MANY-MINUTES-'
_how_many_sols_key = '-HOW-MANY-SOLS-'
_short_trip_time_key = '-SHORT_TRIP-TIME-'
_long_trip_time_key = '-LONG-TRIP-TIME-'

_sol_key = '-SOL-MESSAGE-'

_window = None


def setup():
    configure_game()
    display_game()


def configure_game():
    layout = [
        [sg.Text("Number of robots"), sg.Input(size=(5, 1), key=_how_many_robots_key, default_text='6')],
        [sg.Text("Minutes in game"), sg.Input(size=(5, 1), key=_how_many_minutes_key, default_text='20')],
        [sg.Text("Sols in game"), sg.Input(size=(5, 1), key=_how_many_sols_key, default_text='10')],
        [sg.Text("Short trip time (sec)"), sg.Input(size=(5, 1), key=_short_trip_time_key, default_text='5')],
        [sg.Text("Long trip time (sec)"), sg.Input(size=(5, 1), key=_long_trip_time_key, default_text='20')],

        [sg.Text(size=(40, 1), key='-OUTPUT-')],
        [sg.Button('Ok', bind_return_key=True)]
    ]
    setup_window = sg.Window('Configure the Mars Adventure', layout, font=('Sans', 14), finalize=True)
    event, values = setup_window.read()
    setup_window.close()

    if event == sg.WIN_CLOSED:
        exit(1)

    core.configure(
        int(values[_how_many_robots_key]),
        int(values[_how_many_minutes_key]),
        int(values[_how_many_sols_key]),
        int(values[_short_trip_time_key]),
        int(values[_long_trip_time_key])
    )
    core.activate_robots()


def _connected_key(number):
    return f'-ROBOT-CONNECTED-{number}-'


def _rescue_key(number):
    return f'-ROBOT-RESCUE-{number}-'


def _release_key(number):
    return f'-ROBOT-RELEASE-{number}-'


def _robot_pane(number, last_robot):
    enable = number <= last_robot
    layout = [
        [sg.Button('Connected', key=_connected_key(number), pad=(10, 10)),
         sg.Button('Release', key=_release_key(number), pad=(10, 10), disabled=True)],
        [sg.Column([
            [sg.Button(f'Rescue {number}', size=(15, 1), key=_rescue_key(number), pad=(20, 10), disabled=True)]
        ], justification='center')]
    ]
    return sg.Frame(f'Robot {number}', layout, visible=enable, border_width=1, pad=(20, 10))


def display_game():
    global _window

    first_robot, last_robot = core.get_valid_robots()
    public_ip = get_public_ip.get_public_ip()

    layout = [
        [sg.Text(f"Number of robots: {last_robot}", size=(40, 1), justification='left'),
         sg.Text(f"Public IP: {public_ip}", size=(40, 1), justification='right')],
        [sg.Column([[sg.Text(size=(20, 1), key=_sol_key, font=('Sans', 24), justification='center')]],
                   justification='center')],

        [sg.Column([
            [_robot_pane(1, last_robot), _robot_pane(2, last_robot), _robot_pane(3, last_robot)],
            [_robot_pane(4, last_robot), _robot_pane(5, last_robot), _robot_pane(6, last_robot)]
        ], justification='center')]
    ]
    _window = sg.Window('Shared Science Mars Adventure', layout, font=('Sans', 14), finalize=True)


def run_game():
    core.begin_game()
    first_robot, last_robot = core.get_valid_robots()

    flash = False

    running = True
    while running:
        core.process_queue()

        # Update Sol timer
        sol_now, sol_total, mins_per_sol = core.get_sol()
        if sol_now > sol_total + 1:
            break
        _window[_sol_key].update(f'Sol {sol_now:.1f} of {sol_total:.0f}')

        # Manage Button state
        flash = not flash
        for ix in range(first_robot, last_robot + 1):
            # connected
            color = ('green', None) if core.get_connected(ix) else ('red', None)
            _window[_connected_key(ix)].update(button_color=color)
            # rescue
            rescue = core.get_rescue(ix)
            light = flash and rescue
            color = ('white', 'red') if light else None
            _window[_rescue_key(ix)].update(button_color=color, disabled=not rescue)
            # release
            _window[_release_key(ix)].update(disabled=not core.get_taken(ix))

        # Wait for window events
        # timeout allows the Sol timer to update like a clock
        event, values = _window.read(timeout=500)
        if event == sg.WIN_CLOSED:
            break  # TODO: Verify kill game

        # Process any other events
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            # print('============ Event = ', event, ' ==============')
            # print('-------- Values Dictionary (key=value) --------')
            # for key in values:
            #     print(key, ' = ', values[key])

            key_split = event.strip('-').split('-')
            if len(key_split) == 3 and key_split[0] == 'ROBOT':
                number = int(key_split[2])
                if key_split[1] == 'CONNECTED':
                    if core.get_connected(number):
                        core.disconnect(number)
                    else:
                        core.reconnect(number)
                elif key_split[1] == 'RELEASE':
                    core.release_robot(number)
                elif key_split[1] == 'RESCUE':
                    core.clear_rescue(number)

    _window.close()
