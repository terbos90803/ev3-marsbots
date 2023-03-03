class MockRobot:
    def __init__(self, robot_info):
        self.robot_ip_addr = None
        self.robot_mac_addr = robot_info['btmac']
        self.heard_ip_ad = False
        self.s = None

    def connect(self):
        print('Connected to mock robot')
        self.s = True

    def heard_ad(self):
        return self.heard_ip_ad

    def is_connected(self):
        return self.s is not None

    def set_ip(self, addr):
        self.robot_ip_addr = addr
        self.heard_ip_ad = True
        self.connect()

    def close(self):
        print('Disconnected from mock robot')
        self.s = None

    def send_command(self, command):
        if self.s is not None:
            print("Send data to mock robot:", str(command))
