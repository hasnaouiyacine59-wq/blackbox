from flask import Flask, jsonify
import socket, requests, os

app = Flask(__name__)

SOCKS_PORT   = int(os.environ.get("SOCKS_PORT",   9050))
CONTROL_PORT = int(os.environ.get("CONTROL_PORT", 9051))
API_PORT     = int(os.environ.get("API_PORT",     5000))

def tor_cmd(cmd: bytes) -> tuple:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(("127.0.0.1", CONTROL_PORT))
            s.sendall(b'AUTHENTICATE ""\r\n')
            s.recv(1024)
            s.sendall(cmd)
            resp = s.recv(4096).decode()
            return "250" in resp, resp.strip()
    except Exception as e:
        return False, str(e)

@app.route("/reset-ip")
def reset_ip():
    ok, detail = tor_cmd(b"SIGNAL NEWNYM\r\n")
    return jsonify({"status": "ok" if ok else "error", "detail": detail})

@app.route("/ip")
def get_ip():
    try:
        proxies = {"http": f"socks5h://127.0.0.1:{SOCKS_PORT}", "https": f"socks5h://127.0.0.1:{SOCKS_PORT}"}
        ip = requests.get("https://api.ipify.org", proxies=proxies, timeout=15).text
        return jsonify({"ip": ip})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status")
def status():
    ok, detail = tor_cmd(b"GETINFO status/bootstrap-phase\r\n")
    ready = "PROGRESS=100" in detail
    return jsonify({"bootstrapped": ready, "detail": detail})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_PORT)
