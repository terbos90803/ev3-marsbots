import subprocess
import bluetooth
import socket
from Screen import debug_print


size = 1024 # size of receive buffer
_backlog = 1

# port numbers are arbitrary, but must match between server and client
_tcp_port = 32390
_bt_port = 3


# Get a socket for accepting connections from the server
# returns: listener socket, robot's address (either IPv4 or BT-Mac)
def get_listener_socket():
    # Check to see if the robot is connected to an IP network
    hostname = socket.gethostname()
    host_address = socket.gethostbyname(hostname)
    debug_print('name:', hostname)
    debug_print('IP:', host_address)
    # if the top octet of the IP address is 127, there is no active IP connection
    use_bt = host_address.split('.')[0].strip() == '127'

    if use_bt:
        # Fetch BT MAC address
        cmd = "hciconfig"
        device_id = "hci0"
        sp_result = subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        host_address = sp_result.stdout.split("{}:".format(device_id))[1].split("BD Address: ")[1].split(" ")[0].strip()
        debug_print ('BT Mac:', host_address)

        s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        s.bind((host_address, _bt_port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', _tcp_port))

    s.listen(_backlog)

    return s, host_address
