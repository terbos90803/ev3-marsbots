import threading
import core
import api_host
import control_gui

core.startup()

server = threading.Thread(target=api_host.run_server, daemon=True)
server.start()

control_gui.run_game()

exit(0)
