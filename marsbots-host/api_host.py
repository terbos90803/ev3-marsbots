import flask
from flask import request
import core
import threading

_api_server = None
app = flask.Flask("MarsbotsServer")
# app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Shared Science Marsbot Adventure</h1>
<p>Learn more at <a href="https://sharedscience.org/">Shared Science</a>.</p>'''


@app.route('/api/robot_assignment', methods=['GET'])
def get_robot_assignment():
    name = request.args.get('name')
    robot_number = core.assign_available_robot(name)
    if robot_number:
        return {'status': 'ok', 'robot_number': robot_number}
    else:
        return {'status': 'fail', 'message': 'No available robots'}


@app.route('/api/sol', methods=['GET'])
def get_sol():
    sol = core.get_sol()
    if sol:
        return {'status': 'ok', 'sol': sol[0], 'total_sols': sol[1], 'mins_per_sol': sol[2]}
    return {'status': 'fail', 'message': 'Game not running'}


@app.route('/api/plan', methods=['POST'])
def set_plan():
    form_robot = request.form.get('robot')
    if form_robot:
        robot = int(form_robot)
        plan = request.form.get('plan')
        delay = core.queue_plan(robot, plan)
        if plan:
            app.logger.debug(f'plan:{request.form}')
        else:
            app.logger.debug(f'rescue:{request.form}')
        return {'status': 'ok', 'delay': delay}
    return {'status': 'fail', 'message': 'Missing robot id'}


def _run_server():
    app.run(host="0.0.0.0")


def start():
    global _api_server
    _api_server = threading.Thread(target=_run_server, daemon=True)
    _api_server.start()
