import threading
import core
import api_host
import robot_server
import control_gui

core.startup()

# Start REST api server
api_server = threading.Thread(target=api_host.run_server, daemon=True)
api_server.start()

# Advertise host for robot connections
robots = threading.Thread(target=robot_server.robot_host, daemon=True)
robots.start()

control_gui.run_game()

exit(0)
