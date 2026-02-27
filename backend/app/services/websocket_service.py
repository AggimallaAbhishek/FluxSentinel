from app.extensions import socketio


def emit_alert(payload: dict) -> None:
    socketio.emit("threat_alert", payload, namespace="/alerts")
