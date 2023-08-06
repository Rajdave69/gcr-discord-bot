import flask
from backend import *

app = flask.Flask(__name__, template_folder='./html')


used_states = []

@app.route('/')
async def index():

    res = await args_handler(flask.request.args)
    # res - no_args, error, invalid_args, success, unauthorized_discord_user+

    if res == "success":
        await add_response(flask.request.args.get('state'), "success")
    elif res == "error":
        await add_response(flask.request.args.get('state'), "error")




    return flask.render_template('index.html')



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)