import FreeSimpleGUI as sg
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

# robot assignment keys
_client_frame_key = '-CLIENTS-FRAME'

def _connected_key(number):
    return f'-ROBOT-CONNECTED-{number}-'


def _rescue_key(number):
    return f'-ROBOT-RESCUE-{number}-'

def _robot_assign_key(clientId: str) -> str:
    return f'-CLIENTS-ASSIGN-{clientId}'

def _client_ping_key(clientId: str) -> str:
    return f'-CLIENTS-PING-{clientId}'

def _parse_robot_assign_key(robot_assign_key: str) -> str:
    return robot_assign_key[len('-CLIENTS-ASSIGN-'):]

def _robot_pane(number, label):
    layout = [
        [sg.Button('Disconnected', key=_connected_key(number), pad=(10, 10))],
        [sg.Button(f'Rescue {number}', size=(15, 1), key=_rescue_key(number), pad=(20, 10), disabled=True)]
    ]
    return sg.Frame(f'Robot {number}  -  {label}', layout, border_width=1, pad=(20, 10), element_justification='center')

def _robot_id_to_str(id: int) -> str:
    return f'Robot {id}'

def _robot_id_from_str(formatted: str) -> int:
    return int(formatted[len('Robot '):])

def _client_row(clientId: str, robots: 'list[int]'):
    return [[
        sg.Text(clientId, size=(40, 1)),
        sg.Text("Last ping (sec): ???", size=(20, 1), key=_client_ping_key(clientId)),
        sg.Combo(['NONE'] + [_robot_id_to_str(robot) for robot in robots], default_value='NONE', readonly=True, key=_robot_assign_key(clientId), enable_events=True)
    ]]

def _display_game():
    numbers = core.get_valid_robot_numbers()
    public_ip = get_public_ip.get_public_ip()
    mins, sols, short, long = core.get_game_config()

    robot_panes = []
    row_panes = []
    for num in numbers:
        row_panes.append(_robot_pane(num, core.get_robot_label(num)))
        if len(row_panes) == 3:
            robot_panes.append(row_panes)
            row_panes = []
    if len(row_panes) > 0:
        robot_panes.append(row_panes)

    config_layout = [
        [sg.Column([
            [sg.Text("Minutes in game"), sg.Input(size=(5, 1), key=_how_many_minutes_key, default_text=mins)],
            [sg.Text("Sols in game"), sg.Input(size=(5, 1), key=_how_many_sols_key, default_text=sols)]
        ]), sg.Column([
            [sg.Text("Short trip time (sec)"), sg.Input(size=(5, 1), key=_short_trip_time_key, default_text=short)],
            [sg.Text("Long trip time (sec)"), sg.Input(size=(5, 1), key=_long_trip_time_key, default_text=long)]
        ])]
    ]

    layout = [
        [sg.Text(f"Known robots: {len(numbers)}", size=(40, 1), justification='left'),
         sg.Text(f"Public IP: {public_ip}", size=(40, 1), justification='right')],
        [sg.Frame('Game Configuration', config_layout, key=_config_frame_key, border_width=1, pad=(20, 10))],
        [sg.Button('Start', size=(20, 1), key=_start_button_key),
         sg.Button('Abort', key=_abort_button_key)],
        [sg.Column([[sg.Text(size=(20, 1), key=_sol_key, font=('Sans', 24), justification='center')]],
                   justification='center')],
        [sg.Column(robot_panes, justification='center')],
        [sg.Frame('Clients', [[]], key=_client_frame_key, border_width=1, pad=(20, 10))]
    ]
    window = sg.Window('Shared Science Mars Adventure', layout, font=('Sans', 10),
                       enable_close_attempted_event=True, finalize=True)
    return window


def run_game():
    window = _display_game()
    numbers = core.get_valid_robot_numbers()
    def_color = sg.Button().ButtonColor

    flash = False

    registered_clients: 'set[str]' = set()

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
            # rescue
            rescue = core.get_rescue(num)
            light = flash and rescue
            any_rescues = any_rescues or light
            color = ('white', 'red') if light else def_color
            window[_rescue_key(num)].update(button_color=color, disabled=not rescue)

        if any_rescues:
            sound.alert()

        # Manage robot assignment
        clients = core.get_known_clients()
        for client in clients:
            if client not in registered_clients:
                window.extend_layout(window[_client_frame_key], _client_row(client, numbers))
                registered_clients.add(client)

            last_ping = core.get_last_client_ping(client)
            text = f'Last ping (sec): {last_ping:.1f}' if last_ping else 'Last ping (sec): N/A'
            window[_client_ping_key(client)].update(text)

        # Wait for window events
        # timeout allows the Sol timer to update like a clock and the buttons to flash
        event, values = window.read(timeout=500)
        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT \
                and sg.popup_yes_no('Do you really want to exit?', font=('Sans', 18)) == 'Yes':
            break

        # Keep robots alive
        core.ping_robots()

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
            elif len(key_split) > 2 and key_split[0] == 'CLIENTS' and key_split[1] == 'ASSIGN':
                client = _parse_robot_assign_key(event)
                value = values[event]
                if value == 'NONE':
                    core.release_robot_from_client(client)
                else:
                    robot = _robot_id_from_str(value)
                    core.assign_robot(robot, client)

    window.close()
