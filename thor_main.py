import random, os, string, sys
import argparse
import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
import time
import user_agnt
from xvfbwrapper import Xvfb

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
PROXY_FILE      = os.path.join(BASE_DIR, "proxies.txt")
USED_PROXY_FILE = os.path.join(BASE_DIR, "used_proxies.txt")
LOG_FILE        = os.path.join(BASE_DIR, "ip_log.txt")
REQUEST_TIMEOUT = 15

def _test_proxy(proxy: str, timeout: int) -> bool:
    for url in ["http://api.ipify.org", "http://httpbin.org/ip", "http://ifconfig.me/ip"]:
        try:
            r = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=timeout)
            if r.status_code == 200:
                return True
        except Exception:
            continue
    return False

def get_working_proxy(proxy_list, timeout=REQUEST_TIMEOUT) -> str:
    random.shuffle(proxy_list)
    print(f"[~] Testing {len(proxy_list)} proxies...")
    working = []
    with ThreadPoolExecutor(max_workers=min(len(proxy_list), 20)) as ex:
        futures = {ex.submit(_test_proxy, p, timeout): p for p in proxy_list}
        for f in as_completed(futures):
            if f.result():
                working.append(futures[f])
    if not working:
        raise RuntimeError("No working proxies available!")
    chosen = random.choice(working)
    print(f"✅ {len(working)} working | 🎯 Selected: {chosen}")
    return chosen

def mark_proxy_used(proxy: str):
    with open(PROXY_FILE) as f:
        lines = [l.strip() for l in f if l.strip()]
    remaining = [l for l in lines if not (l == proxy or f"http://{l}" == proxy or l == proxy.replace("http://", ""))]
    with open(PROXY_FILE, "w") as f:
        f.write("\n".join(remaining) + ("\n" if remaining else ""))
    with open(USED_PROXY_FILE, "a") as f:
        f.write(proxy + "\n")
    print(f"[~] Proxy moved to used: {proxy}")

def get_ip_info(proxy_url: str = None, retries: int = 6, delay: int = 5) -> dict:
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    urls = ["http://ipwho.is/", "http://ip-api.com/json", "http://api.ipify.org?format=json"]
    for attempt in range(retries):
        for url in urls:
            try:
                r = requests.get(url, timeout=10, proxies=proxies)
                data = r.json()
                if data.get("ip") or data.get("query"):
                    data.setdefault("ip", data.get("query"))
                    data.setdefault("country_code", data.get("countryCode", "US"))
                    return data
            except Exception as e:
                print(f"[-] IP lookup failed ({url}): {e}")
        print(f"[~] Tor not ready yet, retrying in {delay}s... ({attempt+1}/{retries})")
        time.sleep(delay)
    return {}

CC_LANG = {
    "US": ("en-US", "America/New_York",    "en-US,en;q=0.9"),
    "GB": ("en-GB", "Europe/London",       "en-GB,en;q=0.9"),
    "IT": ("it-IT", "Europe/Rome",         "it-IT,it;q=0.9,en;q=0.8"),
    "DE": ("de-DE", "Europe/Berlin",       "de-DE,de;q=0.9,en;q=0.8"),
    "FR": ("fr-FR", "Europe/Paris",        "fr-FR,fr;q=0.9,en;q=0.8"),
    "ES": ("es-ES", "Europe/Madrid",       "es-ES,es;q=0.9,en;q=0.8"),
    "NL": ("nl-NL", "Europe/Amsterdam",    "nl-NL,nl;q=0.9,en;q=0.8"),
    "PL": ("pl-PL", "Europe/Warsaw",       "pl-PL,pl;q=0.9,en;q=0.8"),
    "BR": ("pt-BR", "America/Sao_Paulo",   "pt-BR,pt;q=0.9,en;q=0.8"),
    "RU": ("ru-RU", "Europe/Moscow",       "ru-RU,ru;q=0.9,en;q=0.8"),
    "TR": ("tr-TR", "Europe/Istanbul",     "tr-TR,tr;q=0.9,en;q=0.8"),
    "JP": ("ja-JP", "Asia/Tokyo",          "ja-JP,ja;q=0.9,en;q=0.8"),
    "CN": ("zh-CN", "Asia/Shanghai",       "zh-CN,zh;q=0.9,en;q=0.8"),
    "SE": ("sv-SE", "Europe/Stockholm",    "sv-SE,sv;q=0.9,en;q=0.8"),
    "MX": ("es-MX", "America/Mexico_City", "es-MX,es;q=0.9,en;q=0.8"),
}

_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("-T", "--tor",        action="store_true")
_parser.add_argument("-P", "--proxy",      action="store_true")
_parser.add_argument("--debug",            action="store_true")
_parser.add_argument("--socks-port",       type=int, default=int(os.environ.get("SOCKS_PORT", 9050)))
_parser.add_argument("--control-port",     type=int, default=int(os.environ.get("CONTROL_PORT", 9051)))
_parser.add_argument("--api-port",         type=int, default=int(os.environ.get("API_PORT", 5000)))
_args, _ = _parser.parse_known_args()

TOR_PROXY    = f"socks5://127.0.0.1:{_args.socks_port}"
CONTROL_PORT = _args.control_port
API_BASE     = f"http://127.0.0.1:{_args.api_port}"

def tor_reset_and_get_ip() -> str:
    # wait for bootstrap via API
    for _ in range(24):  # 2 min max
        try:
            r = requests.get(f"{API_BASE}/status", timeout=5)
            if r.json().get("bootstrapped"):
                break
        except Exception:
            pass
        print(f"[~] Waiting for Tor API on {API_BASE}...")
        time.sleep(5)
    # reset IP via API
    try:
        requests.get(f"{API_BASE}/reset-ip", timeout=5)
    except Exception as e:
        print(f"[-] reset-ip failed: {e}")
    time.sleep(5)
    return get_ip_info(TOR_PROXY).get("ip", "unknown")

def log_ip(ip: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {ip}\n")

def generate_identity():
    name   = ''.join(random.choices(string.ascii_lowercase, k=8))
    number = random.randint(1000, 9999)
    email  = f"kalawssimatrix+{number}@gmail.com"
    print("=" * 40)
    print(f"  Name : {name}")
    print(f"  Email: {email}")
    print("=" * 40)
    return name, email

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

def run_session(elements: dict, session_id: int = 0, proxy_config: dict = None):
    tag = f"[{session_id % 100:02d}]"
    _print = lambda msg: print(f"{tag} {msg}")
    if _args.tor:
        tor_ip = tor_reset_and_get_ip()
        log_ip(tor_ip)
        proxy_config = proxy_config or {"server": TOR_PROXY}
    else:
        tor_ip = "N/A"
        proxy_config = proxy_config or {}

    proxy_url = proxy_config.get("server") if proxy_config else None
    ip_info   = get_ip_info(proxy_url)
    cc        = (ip_info.get("country_code") or "US").upper()
    locale, chosen_tz, _ = CC_LANG.get(cc, CC_LANG["US"])
    lang_primary = locale
    lang_base    = locale.split("-")[0]
    _print(f"IP: {ip_info.get('ip')} | {ip_info.get('country')} ({cc}) → locale={locale} tz={chosen_tz}")
    os.environ["TZ"] = chosen_tz
    time.tzset()

    session_profile = os.path.join(BASE_DIR, f"playwright-profile-{session_id}")
    os.makedirs(session_profile, exist_ok=True)
    os.system(f'rm -rf "{session_profile}"/*')

    EMAIL = elements.get("email")
    NAME  = elements.get("name", "N/A")

    with sync_playwright() as p:
        browser_type    = p.chromium
        chosen_viewport = random.choice(VIEWPORTS)
        chrome_ua       = user_agnt.get_ua(browser_type.name)

        _print("\n" + "═" * 52)
        _print(f"  SESSION #{session_id}")
        _print("═" * 52)
        _print(f"  {'Name':<14}: {NAME}")
        _print(f"  {'Email':<14}: {EMAIL}")
        _print(f"  {'Proxy':<14}: {proxy_url or TOR_PROXY}")
        _print(f"  {'Tor IP':<14}: {tor_ip}")
        _print(f"  {'User-Agent':<14}: {chrome_ua[:55]}...")
        _print(f"  {'Viewport':<14}: {chosen_viewport['width']}x{chosen_viewport['height']}")
        _print(f"  {'Timezone':<14}: {chosen_tz}")
        _print(f"  {'Debug':<14}: {_args.debug}")
        _print("═" * 52 + "\n")

        launch_kwargs = dict(
            headless=False,
            proxy=proxy_config,
            user_agent=chrome_ua,
            viewport=chosen_viewport,
            locale=locale,
            timezone_id=chosen_tz,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080",
            ],
            ignore_default_args=["--enable-automation"],
        )
        if os.path.exists("/usr/bin/google-chrome"):
            launch_kwargs["channel"] = "chrome"

        context = browser_type.launch_persistent_context(session_profile, **launch_kwargs)
        try:
            page = context.pages[0] if context.pages else context.new_page()

            hw_concurrency  = random.choice([2, 4, 8])
            device_memory   = random.choice([2, 4, 8])
            battery_level   = round(random.uniform(0.6, 1.0), 2)
            battery_charging = random.choice(["true", "false"])
            rtt             = random.choice([50, 100, 150])
            downlink        = random.choice([5, 10, 20])
            canvas_salt     = random.randint(1, 255)
            audio_salt      = round(random.uniform(0.001, 0.009), 4)
            tz_offset_map   = {
                "America/New_York": 300, "America/Sao_Paulo": 180, "America/Mexico_City": 360,
                "Europe/London": 0, "Europe/Rome": -60, "Europe/Berlin": -60,
                "Europe/Paris": -60, "Europe/Madrid": -60, "Europe/Amsterdam": -60,
                "Europe/Warsaw": -60, "Europe/Moscow": -180, "Europe/Istanbul": -180,
                "Europe/Stockholm": -60, "Asia/Tokyo": -540, "Asia/Shanghai": -480,
            }
            tz_offset = tz_offset_map.get(chosen_tz, 0)
            webgl_vendors  = [
                ("Intel Inc.",            "Intel Iris OpenGL Engine"),
                ("Intel Inc.",            "Intel Iris Pro OpenGL Engine"),
                ("Intel Inc.",            "Intel HD Graphics 630"),
                ("Intel Inc.",            "Intel UHD Graphics 770"),
                ("Intel Inc.",            "Intel Iris Plus Graphics"),
                ("Intel",                 "Intel(R) UHD Graphics 630"),
                ("Intel",                 "Intel(R) UHD Graphics 620"),
                ("Intel",                 "Intel(R) HD Graphics 520"),
                ("Intel",                 "Intel(R) HD Graphics 620"),
                ("Intel",                 "Intel(R) Iris(R) Xe Graphics"),
                ("Intel",                 "Intel(R) Iris(R) Plus Graphics 640"),
                ("Google Inc.",           "ANGLE (Intel, Mesa Intel(R) UHD Graphics 620, OpenGL 4.6)"),
                ("Google Inc.",           "ANGLE (Intel, Mesa Intel(R) UHD Graphics 630, OpenGL 4.6)"),
                ("Google Inc.",           "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (Intel, Intel(R) Iris(R) Plus Graphics Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (AMD, AMD Radeon RX 570 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (AMD, AMD Radeon RX 6600 XT Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)"),
                ("Google Inc.",           "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0)"),
                ("NVIDIA Corporation",    "NVIDIA GeForce GTX 1050 Ti/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce GTX 1060/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce GTX 1650/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce RTX 2060/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce RTX 2070/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce RTX 3060/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce RTX 3070/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce RTX 3080/PCIe/SSE2"),
                ("NVIDIA Corporation",    "NVIDIA GeForce RTX 4070/PCIe/SSE2"),
                ("ATI Technologies Inc.", "AMD Radeon Pro 5500M OpenGL Engine"),
                ("ATI Technologies Inc.", "AMD Radeon Pro 5600M OpenGL Engine"),
                ("ATI Technologies Inc.", "AMD Radeon Pro 560X OpenGL Engine"),
                ("ATI Technologies Inc.", "AMD Radeon RX 570"),
                ("ATI Technologies Inc.", "AMD Radeon RX 580"),
                ("ATI Technologies Inc.", "AMD Radeon RX 6600 XT"),
                ("ATI Technologies Inc.", "AMD Radeon RX 6700 XT"),
                ("Apple Inc.",            "Apple M1"),
                ("Apple Inc.",            "Apple M1 Pro"),
                ("Apple Inc.",            "Apple M1 Max"),
                ("Apple Inc.",            "Apple M2"),
                ("Apple Inc.",            "Apple M2 Pro"),
                ("Apple Inc.",            "Apple M3"),
                ("Qualcomm",              "Adreno (TM) 618"),
                ("Qualcomm",              "Adreno (TM) 640"),
                ("Qualcomm",              "Adreno (TM) 650"),
                ("Qualcomm",              "Adreno (TM) 660"),
                ("ARM",                   "Mali-G78"),
                ("ARM",                   "Mali-G710"),
            ]
            webgl_vendor, webgl_renderer = random.choice(webgl_vendors)

            page.add_init_script(f"""
                // --- automation flags ---
                Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                window.chrome = {{ runtime: {{}} }};
                Object.defineProperty(navigator, 'plugins', {{ get: () => [1, 2, 3, 4, 5] }});

                // --- language / locale ---
                Object.defineProperty(navigator, 'languages', {{ get: () => ['{lang_primary}', '{lang_base}'] }});
                Object.defineProperty(navigator, 'language',  {{ get: () => '{lang_primary}' }});
                Object.defineProperty(Intl, 'DateTimeFormat', {{
                    value: new Proxy(Intl.DateTimeFormat, {{
                        construct(target, args) {{
                            if (!args[0]) args[0] = '{locale}';
                            return new target(...args);
                        }}
                    }})
                }});

                // --- window geometry ---
                Object.defineProperty(window, 'outerHeight', {{ get: () => window.innerHeight }});
                Object.defineProperty(window, 'outerWidth',  {{ get: () => window.innerWidth  }});
                Object.defineProperty(screen, 'width',       {{ get: () => {chosen_viewport['width']}  }});
                Object.defineProperty(screen, 'height',      {{ get: () => {chosen_viewport['height']} }});
                Object.defineProperty(screen, 'availWidth',  {{ get: () => {chosen_viewport['width']}  }});
                Object.defineProperty(screen, 'availHeight', {{ get: () => {chosen_viewport['height']} }});

                // --- hardware ---
                Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hw_concurrency} }});
                Object.defineProperty(navigator, 'deviceMemory',        {{ get: () => {device_memory}  }});

                // --- canvas noise ---
                const _toDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const noise = (Math.random() - 0.5) * 0.01 + {canvas_salt} / 100000;
                        ctx.fillStyle = `rgba(255,255,255,${{Math.abs(noise)}})`;
                        ctx.fillRect(0, 0, 1, 1);
                    }}
                    return _toDataURL.apply(this, args);
                }};
                const _getImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                    const data = _getImageData.apply(this, args);
                    for (let i = 0; i < data.data.length; i += 100) {{
                        data.data[i] = data.data[i] ^ (Math.random() * 2 | 0);
                    }}
                    return data;
                }};

                // --- WebGL ---
                const _getParam = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(p) {{
                    if (p === 37445) return '{webgl_vendor}';
                    if (p === 37446) return '{webgl_renderer}';
                    return _getParam.call(this, p);
                }};
                const _getParam2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(p) {{
                    if (p === 37445) return '{webgl_vendor}';
                    if (p === 37446) return '{webgl_renderer}';
                    return _getParam2.call(this, p);
                }};

                // --- AudioContext noise ---
                const _createAnalyser = AudioContext.prototype.createAnalyser;
                AudioContext.prototype.createAnalyser = function() {{
                    const analyser = _createAnalyser.call(this);
                    const _getFloatFreq = analyser.getFloatFrequencyData.bind(analyser);
                    analyser.getFloatFrequencyData = function(arr) {{
                        _getFloatFreq(arr);
                        for (let i = 0; i < arr.length; i++) arr[i] += (Math.random() - 0.5) * {audio_salt};
                    }};
                    return analyser;
                }};

                // --- Timezone offset ---
                Date.prototype.getTimezoneOffset = () => {tz_offset};

                // --- Battery ---
                navigator.getBattery = () => Promise.resolve({{
                    charging: {battery_charging}, level: {battery_level},
                    chargingTime: 0, dischargingTime: Infinity,
                    addEventListener: () => {{}}
                }});

                // --- Network ---
                Object.defineProperty(navigator, 'connection', {{ get: () => ({{
                    effectiveType: '4g', rtt: {rtt}, downlink: {downlink}, saveData: false,
                    addEventListener: () => {{}}
                }})}});

                // --- Permissions ---
                const _permQuery = navigator.permissions.query.bind(navigator.permissions);
                navigator.permissions.query = (p) =>
                    p.name === 'notifications'
                        ? Promise.resolve({{ state: 'default' }})
                        : _permQuery(p);

                // --- Speech synthesis ---
                Object.defineProperty(speechSynthesis, 'getVoices', {{ get: () => () => [] }});

                // --- Media devices ---
                if (navigator.mediaDevices) {{
                    navigator.mediaDevices.enumerateDevices = () => Promise.resolve([
                        {{ kind: 'audioinput',  label: '', deviceId: 'default', groupId: 'default' }},
                        {{ kind: 'audiooutput', label: '', deviceId: 'default', groupId: 'default' }},
                        {{ kind: 'videoinput',  label: '', deviceId: 'default', groupId: 'default' }},
                    ]);
                }}

                // --- mimeTypes (proper array-like) ---
                Object.defineProperty(navigator, 'mimeTypes', {{ get: () => {{ return {{ length: 2, 0: {{ type: 'application/pdf' }}, 1: {{ type: 'application/x-google-chrome-pdf' }} }}; }} }});
            """)

            page.goto(f"https://mohmal.eu.org/?{EMAIL}", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)

            for i, frame in enumerate(page.frames[1:][:2]):
                try:
                    frame.click("body", timeout=13000)
                    _print(f"Clicked iframe #{i+1}: {frame.url[:60]}")
                    time.sleep(1)
                    try:
                        text = frame.locator("body").inner_text(timeout=5000).strip()
                        if text:
                            _print(f"iframe #{i+1} text: {text[:300]}")
                    except Exception:
                        pass
                except Exception as e:
                    _print(f"iframe #{i+1} click failed: {e}")
                if i == 0:
                    page.bring_to_front()
                    time.sleep(1)

            page.bring_to_front()
            time.sleep(10)

            for i, pg in enumerate(context.pages):
                try:
                    _print(f"[tab {i}] title: {pg.title()}")
                except Exception:
                    _print(f"[tab {i}] title: <navigating>")

            if len(context.pages) > 1:
                second_tab = context.pages[1]
                second_tab.bring_to_front()
                try:
                    _print(f"Switched to tab 1: {second_tab.title()}")
                except Exception:
                    _print("Switched to tab 1: <navigating>")
                time.sleep(2)
                page.bring_to_front()
                try:
                    _print(f"Back to tab 0: {page.title()}")
                except Exception:
                    _print("Back to tab 0: <navigating>")

            target_handler = page
            for frame in page.frames:
                if "2420628" in frame.url and frame != page.main_frame:
                    target_handler = frame
                    _print(f"Found app frame: {frame.url}")
                    break

            try:
                button = target_handler.locator("button:has-text('Random'), a:has-text('Create'), #create-email")
                button.wait_for(state="visible", timeout=15000)
                button.click()
                _print("Clicked the create button.")
            except Exception as e:
                _print(f"Failed to click mohmal button: {e}")
                page.screenshot(path=os.path.join(BASE_DIR, f"debug_{session_id}_mohmal.png"))

            time.sleep(20)
            _print(f"Current URL: {page.url}")
        finally:
            context.close()


# --- entry point ---
if not _args.tor and not _args.proxy:
    print("[-] Specify -T (Tor) or -P (proxy). Exiting.")
    sys.exit(1)

proxy_config = None
if _args.proxy:
    with open(PROXY_FILE) as f:
        proxies = [l.strip() if "://" in l.strip() else f"http://{l.strip()}" for l in f if l.strip()]
    if not proxies:
        print("[~] proxies.txt empty — restoring from used_proxies.txt")
        with open(USED_PROXY_FILE) as f:
            proxies = [l.strip() for l in f if l.strip()]
        with open(PROXY_FILE, "w") as f:
            f.write("\n".join(proxies) + "\n")
        open(USED_PROXY_FILE, "w").close()
        print(f"[~] Restored {len(proxies)} proxies")
    proxy_url = get_working_proxy(proxies)
    mark_proxy_used(proxy_url)
    print(f"[~] Using proxy: {proxy_url}")
    proxy_config = {"server": proxy_url}

name, email_addr = generate_identity()
session_id = _args.socks_port
with Xvfb(width=1920, height=1080, colordepth=24):
    run_session(elements={"email": email_addr, "name": name}, session_id=session_id, proxy_config=proxy_config)
os.system(f'rm -rf "{os.path.join(BASE_DIR, f"playwright-profile-{session_id}")}"')
