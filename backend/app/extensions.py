from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()

# Python 3.14 is currently incompatible with eventlet; threading mode keeps local dev stable.
socketio = SocketIO(async_mode="threading")
