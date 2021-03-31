import threading
import api_host
import control_gui


control_gui.setup()

server = threading.Thread(target=api_host.run_server, daemon=True)
server.start()

control_gui.run_game()

exit(0)
