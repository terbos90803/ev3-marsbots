import PySimpleGUI as sg
import core
import get_public_ip
import sound


# configure frame keys
_config_frame_key = '-CONFIGURE-'
_how_many_minutes_key = '-HOW-MANY-MINUTES-'
_how_many_sols_key = '-HOW-MANY-SOLS-'
_short_trip_time_key = '-SHORT_TRIP-TIME-'
_long_trip_time_key = '-LONG-TRIP-TIME-'

# main window keys
_start_button_key = '-START-'
_abort_button_key = '-ABORT-'
_sol_key = '-SOL-MESSAGE-'


def _connected_key(number):
    return f'-ROBOT-CONNECTED-{number}-'


def _rescue_key(number):
    return f'-ROBOT-RESCUE-{number}-'


def _release_key(number):
    return f'-ROBOT-RELEASE-{number}-'


def _last_ping_key(number):
    return f'-ROBOT-PING-{number}-'


def _robot_pane(number, label):
    layout = [
        [sg.Button('Disconnected', key=_connected_key(number), pad=(10, 10)),
         sg.Button('Available', key=_release_key(number), pad=(10, 10), disabled=True)],
        [sg.Text(size=(20, 1), key=_last_ping_key(number))],
        [sg.Column([
            [sg.Button(f'Rescue {number}', size=(15, 1), key=_rescue_key(number), pad=(20, 10), disabled=True)]
        ], justification='center')]
    ]
    return sg.Frame(f'Robot {number}  -  {label}', layout, border_width=1, pad=(20, 10))


def _display_game():
    numbers = core.get_valid_robot_numbers()
    public_ip = get_public_ip.get_public_ip()
    mins, sols, short, long = core.get_game_config()

    panes = []
    row_panes = []
    for num in numbers:
        row_panes.append(_robot_pane(num, core.get_robot_label(num)))
        if len(row_panes) == 3:
            panes.append(row_panes)
            row_panes = []
    if len(row_panes) > 0:
        panes.append(row_panes)

    config_layout = [
        [sg.Text("Minutes in game"), sg.Input(size=(5, 1), key=_how_many_minutes_key, default_text=mins)],
        [sg.Text("Sols in game"), sg.Input(size=(5, 1), key=_how_many_sols_key, default_text=sols)],
        [sg.Text("Short trip time (sec)"), sg.Input(size=(5, 1), key=_short_trip_time_key, default_text=short)],
        [sg.Text("Long trip time (sec)"), sg.Input(size=(5, 1), key=_long_trip_time_key, default_text=long)]
    ]
    layout = [
        [sg.Text(f"Known robots: {len(numbers)}", size=(40, 1), justification='left'),
         sg.Text(f"Public IP: {public_ip}", size=(40, 1), justification='right')],
        [sg.Frame('Game Configuration', config_layout, key=_config_frame_key, border_width=1, pad=(20, 10))],
        [sg.Button('Start', size=(20, 1), key=_start_button_key),
         sg.Button('Abort', key=_abort_button_key)],
        [sg.Column([[sg.Text(size=(20, 1), key=_sol_key, font=('Sans', 24), justification='center')]],
                   justification='center')],

        [sg.Column(panes, justification='center')]
    ]
    window = sg.Window('Shared Science Mars Adventure', layout, font=('Sans', 14),
                       enable_close_attempted_event=True, finalize=True)
    return window


def run_game():
    window = _display_game()
    numbers = core.get_valid_robot_numbers()

    flash = False

    running = True
    while running:
        active = core.is_game_running()

        # Process any pending plans or rescues
        core.process_queue()

        # Update Sol timer
        if active:
            sol_now, sol_total, mins_per_sol = core.get_sol()
            if sol_now > sol_total + 1:
                core.abort_game()
            window[_sol_key].update(f'Sol {sol_now:.1f} of {sol_total:.0f}', visible=True)
        else:
            window[_sol_key].update(visible=False)

        # Manage Button states
        window[_config_frame_key].update(visible=not active)
        window[_start_button_key].update(disabled=active)
        window[_abort_button_key].update(disabled=not active)
        any_rescues = False
        flash = not flash
        for num in numbers:
            # connected
            connected = core.get_connected(num)
            color = ('green', None) if connected else ('red', None)
            text = 'Connected' if connected else 'Disconnected'
            window[_connected_key(num)].update(text, button_color=color)
            # release
            name = core.get_player_name(num)
            available = not core.get_taken(num)
            text = 'Available' if available else name if name else 'Release'
            window[_release_key(num)].update(text, disabled=available)
            # last ping
            last_ping = core.get_last_ping(num)
            text = f'Last ping (sec): {last_ping:.0f}' if last_ping and not available else ''
            window[_last_ping_key(num)].update(text)
            # rescue
            rescue = core.get_rescue(num)
            light = flash and rescue
            any_rescues = any_rescues or light
            color = ('white', 'red') if light else None
            window[_rescue_key(num)].update(button_color=color, disabled=not rescue)

        if any_rescues:
            sound.alert()

        # Wait for window events
        # timeout allows the Sol timer to update like a clock and the buttons to flash
        event, values = window.read(timeout=500)
        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT \
                and sg.popup_yes_no('Do you really want to exit?', font=('Sans', 18)) == 'Yes':
            break

        # Process any button events
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            key_split = event.strip('-').split('-')
            if len(key_split) == 3 and key_split[0] == 'ROBOT':
                button = key_split[1]
                number = int(key_split[2])
                if button == 'CONNECTED':
                    if core.get_connected(number):
                        core.disconnect(number)
                    else:
                        core.reconnect(number)
                elif button == 'RELEASE':
                    core.release_robot(number)
                elif button == 'RESCUE':
                    core.clear_rescue(number)
            elif event == _start_button_key:
                core.set_game_config(
                    int(values[_how_many_minutes_key]),
                    int(values[_how_many_sols_key]),
                    int(values[_short_trip_time_key]),
                    int(values[_long_trip_time_key])
                )
                core.start_game()
            elif event == _abort_button_key:
                core.abort_game()

    window.close()
