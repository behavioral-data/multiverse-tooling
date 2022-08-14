from flask import Flask
# from flask_socketio import SocketIO
# from apscheduler.schedulers.background import BackgroundScheduler

app_diff = Flask(__name__, static_folder='resources', static_url_path='')
app_error_dashboard =  Flask(__name__, static_folder='resources', static_url_path='')
# socketio = SocketIO(app)
# scheduler = BackgrsoundScheduler()

if __name__ == "__main__":
    app_diff.run(host='127.0.0.1', port=8080)
