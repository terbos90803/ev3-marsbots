import socket
import threading
import core

_ad_port = 32391
_ad_socket = None
_ad_mon_thread = None


def _run_monitor():
    while True:
        data, addr_port = _ad_socket.recvfrom(1024)
        # print("received message: {} from {}".format(data, addr_port))
        name = data.decode('utf-8')
        addr = addr_port[0]
        print(f'Found robot {name} at {addr}')
        core.found_robot(name, addr)


def start():
    global _ad_socket, _ad_mon_thread

    _ad_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP

    # Enable port reusage so we will be able to run multiple clients and servers on single (host, port).
    # Do not use socket.SO_REUSEADDR except you using linux(kernel<3.9): goto https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ for more information.
    # For linux hosts all sockets that want to share the same address and port combination must belong to processes that share the same effective user ID!
    # So, on linux(kernel>=3.9) you have to run multiple servers and clients under one user to share the same (host, port).
    # Thanks to @stevenreddie
    # _ad_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Enable broadcasting mode
    _ad_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    _ad_socket.bind(('', _ad_port))
    print("Monitoring for IP robots")

    _ad_mon_thread = threading.Thread(target=_run_monitor, daemon=True)
    _ad_mon_thread.start()
