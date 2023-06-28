import flask
from backend import *

app = flask.Flask(__name__, template_folder='./html')


used_states = []

@app.route('/')
async def index():

    res = await args_handler(flask.request.args)
    # res - no_args, error, invalid_args, success, unauthorized_discord_user




    return flask.render_template('index.html')



