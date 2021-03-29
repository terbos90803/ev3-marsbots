import PySimpleGUI as sg
import core
import get_public_ip

_how_many_robots_key = '-HOW-MANY-ROBOTS-'
_how_many_minutes_key = '-HOW-MANY-MINUTES-'
_how_many_sols_key = '-HOW-MANY-SOLS-'
_short_trip_time_key = '-SHORT_TRIP-TIME-'
_long_trip_time_key = '-LONG-TRIP-TIME-'

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


def display_game():
    global _window

    first_robot, last_robot = core.get_valid_robots()
    public_ip = get_public_ip.get_public_ip()

    layout = [
        [sg.Text(f"Number of robots: {last_robot}", size=(25,1), justification='left'),
         sg.Text(f"Public IP: {public_ip}", size=(25,1), justification='right')],
        [sg.Text("Sols in game"), sg.Input(size=(5, 1), key=_how_many_sols_key, default_text='10')],
        [sg.Text("Short trip time (sec)"), sg.Input(size=(5, 1), key=_short_trip_time_key, default_text='5')],
        [sg.Text("Long trip time (sec)"), sg.Input(size=(5, 1), key=_long_trip_time_key, default_text='20')],

        [sg.Text(size=(40, 1), key='-OUTPUT-')],
        [sg.Button('Ok', bind_return_key=True)]
    ]
    _window = sg.Window('Shared Science Mars Adventure', layout, font=('Sans', 14), finalize=True)


def run_game():
    running = True
    while running:
        # Wait for window events
        # timeout allows the Sol timer to update like a clock
        event, values = _window.read(timeout=500)
        if event == sg.WIN_CLOSED:
            break  # TODO: Verify kill game

        # Process any other events
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            print('============ Event = ', event, ' ==============')
            print('-------- Values Dictionary (key=value) --------')
            for key in values:
                print(key, ' = ', values[key])

    _window.close()
