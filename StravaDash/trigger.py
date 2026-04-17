from flask import Flask, request
import subprocess

app = Flask(__name__)

SECRET = "25123615.mEr"

@app.route("/refresh")
def refresh():
    token = request.args.get("token")
    if token != SECRET:
        return "Forbidden", 403

    subprocess.Popen([
        r"C:\Users\Plex\Dropbox\Cycling\StravaDash\run.bat"
    ])

    return "Refresh started", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)