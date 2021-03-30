import flask
from flask import request
import core

app = flask.Flask("MarsbotsServer")
# app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Shared Science Marsbot Adventure</h1>
<p>Learn more at <a href="https://sharedscience.org/">Shared Science</a>.</p>'''


@app.route('/robots', methods=['GET'])
def get_valid_robots():
    first_robot, last_robot = core.get_valid_robots()
    return {'status': 'ok', 'first_robot': first_robot, 'last_robot': last_robot}


@app.route('/robot', methods=['POST'])
def register_robot():
    if 'robot' in request.form:
        robot = int(request.form['robot'])
        if core.take_robot(robot):
            return {'status': 'ok'}
        app.logger.error(f'Duplicate robot registration:{robot}')
        return {'status': 'fail', 'reason': 'Number already taken'}
    else:
        app.logger.error('Missing robot id for registration')
        return {'status': 'fail', 'reason': 'Missing robot id'}


@app.route('/sol', methods=['GET'])
def get_sol():
    sol_now, total_sols, mins_per_sol = core.get_sol()
    return {'status': 'ok', 'sol': sol_now, 'total_sols': total_sols, 'mins_per_sol': mins_per_sol}


@app.route('/plan', methods=['POST'])
def set_plan():
    form_robot = request.form.get('robot')
    if form_robot is not None:
        robot = int(form_robot)
        plan = request.form.get('plan')
        delay = core.queue_plan(robot, plan)
        if plan is not None:
            app.logger.debug(f'plan:{request.form}')
        else:
            app.logger.debug(f'rescue:{request.form}')
        return {'status': 'ok', 'delay': delay}
    return {'status': 'fail', 'reason': 'Missing robot id'}


def run_server():
    app.run(host="0.0.0.0")
