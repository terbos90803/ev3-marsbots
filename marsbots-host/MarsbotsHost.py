import core
import ad_monitor
import api_host
import control_gui

core.startup()

# Start server threads
api_host.start()
ad_monitor.start()

control_gui.run_game()

core.shutdown()

exit(0)
