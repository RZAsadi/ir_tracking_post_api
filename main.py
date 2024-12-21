from flask import Flask
from tracking import TrackingService
import logging
import os

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "56567"))

log = logging.getLogger('werkzeug')
log.setLevel(logging.CRITICAL)


app = Flask(__name__)
track_post = TrackingService()

@app.route("/track/<post_track_code>")
def track(post_track_code):
    if len(post_track_code) < 24: return {"success": False, "ERROR": "The barcode must be 24 characters"}
    result = track_post.search_tracking(post_track_code)
    if result:
        return result
    else:
        return {"success": False, "ERROR": "The barcode is invalid"}

app.run(host=HOST, port=PORT, debug=False)