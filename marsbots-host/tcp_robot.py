import socket
import pickle


class TcpRobot:
    def __init__(self, robot_ip_addr):
        self.robot_ip_addr = robot_ip_addr
        self.port = 32390  # port number is arbitrary, but must match between server and client
        self.s = None

    def connect(self):
        if not self.s:
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((self.robot_ip_addr, self.port))
                print('Connected to robot', self.robot_ip_addr)
            except OSError as err:
                self.s = None
                print(f'Failed to open TCP connection to {self.robot_ip_addr}: {repr(err)}')

    def is_connected(self):
        return self.s is not None

    def close(self):
        if self.s is not None:
            self.send_command(None)
            if self.s is not None:
                self.s.close()
            self.s = None

    def send_command(self, command):
        if self.s is not None:
            data = pickle.dumps(command, protocol=3)
            try:
                self.s.sendall(data)
            except OSError:
                self.s = None
                print('Robot disconnected', self.robot_ip_addr)
