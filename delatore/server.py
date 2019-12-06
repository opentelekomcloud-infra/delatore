from argparse import ArgumentParser

from flask import Flask, jsonify, request

from delatore.bot import Delatore

app = Flask(__name__)
bot = Delatore()


@app.route('/')
def index():
    return 'OK'


@app.route('/notifications', methods=['POST'])
def awx_notifications():
    if request.method == 'POST':
        response = request.get_json()
        bot.send_notification(response)
        return jsonify(response)


def main():
    """Main handler"""
    _arg_parser = ArgumentParser(description="Service handling requests to delatore-bot")
    _arg_parser.add_argument("--port", help="port to be listened", default=23456, type=int)
    args = _arg_parser.parse_args()
    app.run(port=args.port, debug=True)


if __name__ == '__main__':
    main()
