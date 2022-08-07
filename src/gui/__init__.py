from flask import Flask
# from flask_socketio import SocketIO
# from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder='resources', static_url_path='')
# socketio = SocketIO(app)
# scheduler = BackgrsoundScheduler()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)
