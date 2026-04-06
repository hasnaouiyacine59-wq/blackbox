
➜  workspace git:(main) ✗ history
   cd tor-proxy-1 && docker build -t tor-proxy . && docker run -d   --name tor-proxy   -p 5000:5000   -p 9050:9050   tor-proxy && cd ../tor-proxy-2 && docker build -t tor-proxy2 . && docker run -d   --name tor-proxy2   -p 5005:5005   -p 9055:9055   tor-proxy2 && cd ../ad-1 && while true ; do python3 thor_main.py -T --tor-port 9050 --api-port 5000 ; done
      
      && cd ../ad-2 && while true ; do python3 thor_main.py -T --tor-port 9055 --api-port 5005 ; done 




cd ad-2 && while true ; do python3 thor_main.py -T --tor-port 9055 --api-port 5005 ; done 




cd ads-sandbox/ && sudo ./go_go.sh






YJjjbdUTg8hYNNXyZjrxHdOGHQ4ww8FUKNbDCeGO3MkEN77R
kpzOt-hxIRq8ZJ40BnKuycT92wLT0hnEBu-jMULb36Z5W1uj
l7m1XGBjaTp1ZUYV9AFPOVGs-LyoEZimZYdR3KJ4_ZRb-CoJ



{
  // These tasks will run in order when initializing your CodeSandbox project.
  "setupTasks": [],

  // These tasks can be run from CodeSandbox. Running one will open a log in the app.
  "tasks": {
    "whereis htop": {
      "name": "lol htop",
      "command": "pwd && apt-get update -y && apt-get install -y tor torsocks python3-pip xvfb && pip3 install -r requirements.txt && playwright install chrome || true && playwright install-deps",
      "runAtStart": true
    }
  }
}


# tor-proxy

A Dockerized Tor SOCKS5 proxy with a Flask HTTP control API.

## Files

| File | Description |
|------|-------------|
| `Dockerfile` | Builds the image (Debian + Tor + Flask) |
| `torrc` | Tor configuration (SOCKS on 9050, control on 9051) |
| `api.py` | Flask API on port 5000 to control Tor |
| `start.sh` | Entrypoint: starts Tor then the API |

## Requirements

- Docker

## Build

```bash
docker build -t tor-proxy .
```

## Run

```bash

docker build -t tor-proxy . && docker run -d \
  --name tor-proxy \
  -p 5000:5000 \
  -p 9050:9050 \
  tor-proxy
&& docker run -d \
  --name tor-proxy \
  -p 5005:5005 \
  -p 9055:9052 \
  tor-proxy
```

| Port | Purpose |
|------|---------|
| `9050` | Tor SOCKS5 proxy |
| `5000` | Control API |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /ip` | Get current Tor exit node IP |
| `GET /reset-ip` | Request a new Tor circuit (new identity) |
| `GET /restart` | Reload Tor config |
| `GET /stop` | Shutdown Tor |
| `GET /start` | Check if Tor is running |

### Examples

```bash
# Get current exit IP
curl http://localhost:5000/ip

# Rotate to a new exit node
curl http://localhost:5000/reset-ip

# Wait a few seconds after reset, then verify new IP
sleep 5 && curl http://localhost:5000/ip
```

## Use as SOCKS5 Proxy

Point any SOCKS5-compatible app to:

```
socks5h://localhost:9050
```

The `h` in `socks5h` ensures DNS is resolved through Tor (recommended).

### Python (requests)

```python
proxies = {
    "http":  "socks5h://localhost:9050",
    "https": "socks5h://localhost:9050",
}
requests.get("https://example.com", proxies=proxies)
```

## Stop / Remove

```bash
docker stop tor-proxy
docker rm tor-proxy
```

## Notes

- After calling `/reset-ip`, wait ~5 seconds before the new circuit is ready
- The control port (9051) has no authentication — do not expose it publicly
- The API (port 5000) has no authentication — restrict access if deploying remotely
