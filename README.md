# bino_att — Canva Account Automation
docker build -t quay.io/mylastres0rt05/tor-proxy:latest tor-proxy/ && \
docker build --build-arg PLAYWRIGHT_TAG=v1.44.0-jammy -t quay.io/mylastres0rt05/thor-session:v1.44 . && \
docker build --build-arg PLAYWRIGHT_TAG=v1.43.0-jammy -t quay.io/mylastres0rt05/thor-session:v1.43 . && \
docker build --build-arg PLAYWRIGHT_TAG=v1.42.0-jammy -t quay.io/mylastres0rt05/thor-session:v1.42 . && \
docker build --build-arg PLAYWRIGHT_TAG=v1.41.0-jammy -t quay.io/mylastres0rt05/thor-session:v1.41 . && \
docker build --build-arg PLAYWRIGHT_TAG=v1.40.0-jammy -t quay.io/mylastres0rt05/thor-session:v1.40 . && \
docker build --build-arg PLAYWRIGHT_TAG=v1.39.0-jammy -t quay.io/mylastres0rt05/thor-session:v1.39 . && \
docker push quay.io/mylastres0rt05/tor-proxy:latest && \
docker push quay.io/mylastres0rt05/thor-session:v1.44 && \
docker push quay.io/mylastres0rt05/thor-session:v1.43 && \
docker push quay.io/mylastres0rt05/thor-session:v1.42 && \
docker push quay.io/mylastres0rt05/thor-session:v1.41 && \
docker push quay.io/mylastres0rt05/thor-session:v1.40 && \
docker push quay.io/mylastres0rt05/thor-session:v1.39 2>&1 | tail -20 
Automates Canva account creation via email verification, using rotating proxies and anti-detection techniques.

## Project Files

| File | Description |
|------|-------------|
| `main.py` | Main script — uses proxies from `proxies.txt` |
| `thor_main.py` | Tor variant — routes traffic through Tor Docker container |
| `read_mail.py` | Reads verification code from Gmail via IMAP |
| `user_agnt.py` | User-agent pool with `get_ua(browser)` helper |
| `proxies.txt` | List of proxies (HTTP or SOCKS5) |
| `requirements.txt` | Python dependencies |

---

## Requirements

- Python 3.8+
- Google Chrome installed (used via `channel="chrome"`)
- Docker (only for `thor_main.py`)

---

## Installation

### 1. Clone / copy the project

```bash
cp -r bino_att/ /your/target/path/
cd /your/target/path/bino_att/
```

### 2. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Install Playwright browsers

```bash
playwright install chrome
```

> If `playwright` command is not found: `python3 -m playwright install chrome`

### 4. Install system dependencies for Playwright (Linux)

```bash
playwright install-deps
```

---

## Configuration

### proxies.txt

Add one proxy per line. Supports HTTP and SOCKS5:

```
http://1.2.3.4:8080
socks5://1.2.3.4:1080
1.2.3.4:3128          # auto-prefixed as http://
```

### read_mail.py

Edit the credentials at the top of the file:

```python
USERNAME  = "your_gmail@gmail.com"
PASSWORD  = "your_app_password"      # Gmail App Password, not your login password
from_email = "expected_sender@domain.com"
```

> To generate a Gmail App Password: Google Account → Security → 2-Step Verification → App Passwords

---

## Run

### Standard (proxy from proxies.txt)

```bash
python3 main.py
```

### Tor variant (requires Tor Docker container running)

```bash
# Start Tor proxy first
docker run -d --name tor-proxy -p 5000:5000 -p 9050:9050 tor-proxy

# Then run
python3 thor_main.py
```

### Debug mode (shows browser window)

```bash
python3 main.py --debug
python3 thor_main.py --debug
```

---

## How It Works

1. Resets Tor IP / selects a working proxy
2. Opens Google Chrome via Playwright
3. Visits `mohmal.eu.org` (temp email warmup)
4. Navigates to `canva.com/login`
5. Clicks "Continue with email", fills in the generated Gmail alias
6. Waits for the 6-digit verification code via IMAP
7. Submits the code to complete login

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No working proxies available!` | Check `proxies.txt` — test proxies manually with `curl --proxy ...` |
| `playwright._impl._errors.Error: Executable doesn't exist` | Run `playwright install chrome` |
| `Auth failed` on Gmail | Use an App Password, not your account password |
| Canva returns 403 on `_ajax/profile/authentication/options` | Proxy IP is blacklisted — try different proxies |
| `channel="chrome"` error | Install Google Chrome: `apt install google-chrome-stable` or download from google.com/chrome |
