import threading
import core
import api_host
import control_gui

core.startup()

# Start REST api server
api_server = threading.Thread(target=api_host.run_server, daemon=True)
api_server.start()

control_gui.run_game()

core.shutdown()

exit(0)
