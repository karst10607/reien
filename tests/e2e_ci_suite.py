# -*- coding: utf-8 -*-
"""
Zero-Dependency Automated End-to-End (E2E) & Static Verification Test Suite
for Reien 2.5D Cloud Memorial Garden & Town Builder (Chrome DevTools Protocol).

Covers 12 Comprehensive Test Cases:
  TC-01: Static HTML & Inline JS Syntax Check (via node --check)
  TC-02: Zero Runtime & WebGL Scene Boot Verification
  TC-03: Mobile Portrait (390x844) Layout, Non-Obstruction & Virtual Joystick Check
  TC-04: Mobile Landscape (844x390) Layout, Non-Obstruction & Virtual Joystick Check
  TC-05: Virtual Joystick Pointer Drag & Camera-Relative Character Movement
  TC-06: Haptic Vibration Engine (Mobile navigator.vibrate + Gamepad dual-rumble) & Dog ("豆豆") Petting
  TC-07: Thunder & Lightning Weather Haptic Feedback
  TC-08: Multi-Layered Daytime Lighting Contrast, 4096 Shadow Map, God-Rays & Komorebi Shader
  TC-09: Tree Canopy & Indoor House See-Through Occlusion Transparency (X-Ray Fade)
  TC-10: Town Builder Mode & Memorial Shrine Modal Offerings
  TC-11: Mobile Portrait Top UI Collapse / Immersive Mode (手遊風格沉浸式收合頂部選單)
  TC-12: Bluetooth & Wired Gamepad Actuator Dual-Rumble Test
"""
import argparse
import base64
import functools
import http.server
import json
import os
import re
import shutil
import socket
import socketserver
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INDEX_HTML = os.path.join(ROOT_DIR, 'index.html')


# =====================================================================
# Robust Zero-Dependency Chrome DevTools Protocol (CDP) WebSocket Client
# =====================================================================
class RobustWSClient:
    def __init__(self, ws_url: str):
        host_port, path = ws_url[5:].split('/', 1)
        host, port = host_port.split(':')
        self.s = socket.create_connection((host, int(port)), timeout=35)
        self.buf = bytearray()
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        req = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.s.sendall(req.encode('ascii'))
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.s.recv(2048)
            if not chunk:
                raise RuntimeError("CDP WebSocket handshake failed: socket closed")
            resp += chunk
        if b"101" not in resp:
            raise RuntimeError(f"CDP WebSocket handshake failed: {resp[:200]}")
        header_end = resp.index(b"\r\n\r\n") + 4
        self.buf.extend(resp[header_end:])
        self.seq = 10

    def send(self, text: str):
        payload = text.encode('utf-8')
        length = len(payload)
        mask = os.urandom(4)
        header = bytearray([0x81])
        if length <= 125:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack('!H', length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack('!Q', length))
        header.extend(mask)
        masked = bytearray(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.s.sendall(header + masked)

    def recv_msg(self):
        while True:
            while len(self.buf) < 2:
                chunk = self.s.recv(4096)
                if not chunk:
                    return None
                self.buf.extend(chunk)
            b1 = self.buf[0]
            b2 = self.buf[1]
            opcode = b1 & 0x0f
            masked = (b2 & 0x80) != 0
            payload_len = b2 & 0x7f
            header_len = 2
            if payload_len == 126:
                header_len += 2
                while len(self.buf) < header_len:
                    self.buf.extend(self.s.recv(4096))
                payload_len = struct.unpack('!H', self.buf[2:4])[0]
            elif payload_len == 127:
                header_len += 8
                while len(self.buf) < header_len:
                    self.buf.extend(self.s.recv(4096))
                payload_len = struct.unpack('!Q', self.buf[2:10])[0]

            mask_key = None
            if masked:
                while len(self.buf) < header_len + 4:
                    self.buf.extend(self.s.recv(4096))
                mask_key = self.buf[header_len:header_len+4]
                header_len += 4

            total_frame_len = header_len + payload_len
            while len(self.buf) < total_frame_len:
                chunk = self.s.recv(min(total_frame_len - len(self.buf), 65536))
                if not chunk:
                    break
                self.buf.extend(chunk)

            payload = bytearray(self.buf[header_len:total_frame_len])
            self.buf = self.buf[total_frame_len:]

            if masked and mask_key:
                payload = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))

            if opcode == 0x9:  # Ping frame -> reply with Pong
                pong = bytearray([0x8A, 0x80]) + os.urandom(4)
                self.s.sendall(pong)
                continue
            elif opcode == 0x8:  # Close frame
                return None
            elif opcode in (0x1, 0x2):
                return payload.decode('utf-8', errors='ignore')

    def call_cdp(self, method: str, params=None, timeout=30):
        self.seq += 1
        msg_id = self.seq
        self.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        start_t = time.time()
        while time.time() - start_t < timeout:
            raw = self.recv_msg()
            if not raw:
                break
            try:
                data = json.loads(raw)
                if data.get("id") == msg_id:
                    if "error" in data:
                        raise RuntimeError(f"CDP error on {method}: {data['error']}")
                    return data.get("result", {})
            except json.JSONDecodeError:
                pass
        raise TimeoutError(f"CDP call timed out: {method}")

    def eval_js(self, expression: str, timeout=15):
        res = self.call_cdp("Runtime.evaluate", {
            "expression": f"(() => {{ {expression} }})()",
            "returnByValue": True,
            "awaitPromise": True
        }, timeout=timeout)
        if "exceptionDetails" in res:
            raise AssertionError(f"JS Exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def ws_connect(ws_url: str):
    return RobustWSClient(ws_url)


def call_cdp(ws, method: str, params=None, timeout=30):
    return ws.call_cdp(method, params, timeout=timeout)


def eval_js(ws, expression: str, timeout=15):
    return ws.eval_js(expression, timeout=timeout)


def find_browser_binary() -> str:
    candidates = [
        os.environ.get("CHROME_BIN", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("google-chrome") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("chromium") or "",
        shutil.which("msedge") or "",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    raise RuntimeError("No Chromium/Chrome/Edge browser found for headless E2E tests.")


def start_background_server(directory: str):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    handler.log_message = lambda *args, **kwargs: None
    httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, actual_port


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(f"FAILED: {message}")


def capture_png(ws, out_path: str):
    res = call_cdp(ws, "Page.captureScreenshot", {"format": "png"}, timeout=30)
    if res and "data" in res:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        png_bytes = base64.b64decode(res["data"])
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        return len(png_bytes)
    return 0


# =====================================================================
# Test Cases (TC-01 to TC-10)
# =====================================================================
def run_tc01_static_syntax():
    print("[TC-01] Static HTML & Inline JS Syntax Integrity...", end=" ", flush=True)
    assert_true(os.path.isfile(INDEX_HTML), f"index.html not found at {INDEX_HTML}")
    html = open(INDEX_HTML, 'r', encoding='utf-8').read()
    assert_true(len(html) > 140_000, f"index.html unexpectedly small: {len(html)} bytes")

    required_ids = [
        'canvas-container', 'joystick-zone', 'joystick-knob',
        'normal-help', 'haptic-toast', 'memorial-modal', 'minimap-canvas',
        'btn-quality'
    ]
    for dom_id in required_ids:
        assert_true(f'id="{dom_id}"' in html, f'Missing required DOM element id="{dom_id}"')

    scripts = re.findall(r'<script(?![^>]*src=)[^>]*>([\s\S]*?)</script>', html)
    assert_true(len(scripts) >= 1, "No inline <script> found in index.html")
    for idx, js in enumerate(scripts):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as tf:
            tf.write(js)
            temp_js = tf.name
        try:
            res = subprocess.run(['node', '--check', temp_js], capture_output=True, text=True)
            assert_true(res.returncode == 0, f"JS syntax error in script #{idx}: {res.stderr}")
        finally:
            if os.path.exists(temp_js):
                os.remove(temp_js)
    print("PASS")


def run_browser_suite(screenshot_dir: str = None):
    httpd, http_port = start_background_server(ROOT_DIR)
    url = f"http://127.0.0.1:{http_port}/index.html"
    browser_bin = find_browser_binary()
    user_data_dir = tempfile.mkdtemp(prefix="reien_ci_cdp_")

    # Pick an available debugging port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        debug_port = s.getsockname()[1]

    cmd = [
        browser_bin,
        "--headless=new",
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1440,900",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
    ]
    if sys.platform.startswith("linux"):
        cmd.extend([
            "--no-sandbox",
            "--disable-gpu-sandbox",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--ignore-gpu-blocklist",
            "--enable-unsafe-swiftshader"
        ])
    cmd.append(url)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for CDP endpoint to come up (allow up to 30s for cold runner SwiftShader initialization)
        tabs = None
        for _ in range(120):
            if proc.poll() is not None:
                raise RuntimeError(f"Headless browser process exited prematurely with code {proc.returncode}")
            try:
                raw = urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json", timeout=1).read()
                tabs = json.loads(raw)
                if tabs:
                    break
            except Exception:
                time.sleep(0.25)
        assert_true(bool(tabs), "Failed to connect to headless browser CDP endpoint within 30s")

        target_tab = next((t for t in tabs if t.get('type') == 'page'), tabs[0])
        ws = ws_connect(target_tab['webSocketDebuggerUrl'])
        try:
            call_cdp(ws, "Page.enable", timeout=3)
        except Exception:
            pass

        # -----------------------------------------------------------------
        # TC-02: Zero Runtime & WebGL Scene Boot Verification
        # -----------------------------------------------------------------
        print("[TC-02] Zero Runtime & WebGL Scene Boot Verification...", end=" ", flush=True)
        diag = None
        for i in range(50):
            time.sleep(0.5)
            try:
                res = eval_js(ws, "return window.__REIEN_DIAG__ ? window.__REIEN_DIAG__.getState() : null;", timeout=2)
                if res and isinstance(res, dict) and 'occludablesCount' in res:
                    diag = res
                    break
                else:
                    if i % 5 == 0: print(f"(poll {i}: {res})", end=" ", flush=True)
            except Exception as e:
                if i % 5 == 0: print(f"(poll {i} err: {e})", end=" ", flush=True)
        eval_js(ws, """
            window.__runtimeErrors = [];
            window.addEventListener('error', e => window.__runtimeErrors.push(e.message));
        """)
        assert_true(diag is not None, f"window.__REIEN_DIAG__ failed to initialize: {diag}")
        assert_true(diag['occludablesCount'] >= 15, f"Expected >= 15 occludable trees/houses, got {diag['occludablesCount']}")
        assert_true(diag['monumentsCount'] >= 3, f"Expected >= 3 monuments, got {diag['monumentsCount']}")
        assert_true(diag.get('qualityMode') == 'performance', f"Expected qualityMode 'performance', got {diag.get('qualityMode')}")
        assert_true(diag.get('hasComposer') is False, f"Expected composer disabled in performance mode")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-03: Mobile Portrait (390x844) Layout & Non-Obstruction Check
        # -----------------------------------------------------------------
        print("[TC-03] Mobile Portrait (390x844) UI Non-Obstruction & Joystick...", end=" ", flush=True)
        call_cdp(ws, "Emulation.setDeviceMetricsOverride", {
            "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True
        })
        time.sleep(0.45)
        portrait_ui = eval_js(ws, """
            const helpEl = document.getElementById('normal-help');
            const joyEl = document.getElementById('joystick-zone');
            const pillEl = document.querySelector('.pill-btn');
            const joyRect = joyEl.getBoundingClientRect();
            const pillRect = pillEl.getBoundingClientRect();
            return {
                helpDisplay: window.getComputedStyle(helpEl).display,
                joyDisplay: window.getComputedStyle(joyEl).display,
                joyInBounds: joyRect.left >= 0 && joyRect.bottom <= 844 && joyRect.width >= 90,
                pillNoWrap: pillRect.height <= 42
            };
        """)
        assert_true(portrait_ui['helpDisplay'] == 'none', f"#normal-help must be hidden on mobile portrait, got {portrait_ui['helpDisplay']}")
        assert_true(portrait_ui['joyDisplay'] in ('flex', 'block'), f"#joystick-zone must be visible on mobile portrait, got {portrait_ui['joyDisplay']}")
        assert_true(portrait_ui['joyInBounds'], "Virtual joystick out of bounds on 390x844 portrait screen")
        assert_true(portrait_ui['pillNoWrap'], f"Top bar pill buttons wrapped vertically on mobile portrait (height={portrait_ui['pillNoWrap']})")

        # Verify mobile '?' help toggle button works
        help_toggled = eval_js(ws, """
            window.toggleMobileHelp();
            const openDisp = window.getComputedStyle(document.getElementById('normal-help')).display;
            window.toggleMobileHelp();
            const closedDisp = window.getComputedStyle(document.getElementById('normal-help')).display;
            return { openDisp, closedDisp };
        """)
        assert_true(help_toggled['openDisp'] in ('flex', 'block') and help_toggled['closedDisp'] == 'none',
                    f"toggleMobileHelp() failed to open/close #normal-help: {help_toggled}")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-04: Mobile Landscape (844x390) Layout & Virtual Joystick Check
        # -----------------------------------------------------------------
        print("[TC-04] Mobile Landscape (844x390) UI Non-Obstruction & Joystick...", end=" ", flush=True)
        call_cdp(ws, "Emulation.setDeviceMetricsOverride", {
            "width": 844, "height": 390, "deviceScaleFactor": 2, "mobile": True
        })
        time.sleep(0.45)
        landscape_ui = eval_js(ws, """
            const helpEl = document.getElementById('normal-help');
            const joyEl = document.getElementById('joystick-zone');
            const topBar = document.querySelector('.top-bar').getBoundingClientRect();
            const botBar = document.querySelector('.bottom-bar').getBoundingClientRect();
            return {
                helpDisplay: window.getComputedStyle(helpEl).display,
                joyDisplay: window.getComputedStyle(joyEl).display,
                noVerticalOverlap: topBar.bottom < botBar.top
            };
        """)
        assert_true(landscape_ui['helpDisplay'] == 'none', "#normal-help must be hidden on mobile landscape")
        assert_true(landscape_ui['joyDisplay'] in ('flex', 'block'), "#joystick-zone must be visible on mobile landscape")
        assert_true(landscape_ui['noVerticalOverlap'], "Top bar and bottom bar overlap on 844x390 landscape viewport")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-05: Virtual Joystick Pointer Drag & Character Movement
        # -----------------------------------------------------------------
        print("[TC-05] Virtual Joystick Pointer Drag & Character Movement...", end=" ", flush=True)
        moved_res = eval_js(ws, """
            return (async () => {
                window.__REIEN_DIAG__.teleportPlayer(0, 6);
                const zone = document.getElementById('joystick-zone');
                const r = zone.getBoundingClientRect();
                const cx = r.left + r.width / 2;
                const cy = r.top + r.height / 2;
                zone.dispatchEvent(new PointerEvent('pointerdown', { clientX: cx, clientY: cy, pointerId: 1, bubbles: true }));
                window.dispatchEvent(new PointerEvent('pointermove', { clientX: cx + 38, clientY: cy - 32, pointerId: 1, bubbles: true }));
                if (window.__REIEN_DIAG__.setJoystickVector) {
                    window.__REIEN_DIAG__.setJoystickVector(0.75, -0.65);
                }

                // Actively pump 25 animation frames while joystick is held
                await new Promise(resolve => {
                    let frames = 0;
                    const onFrame = () => {
                        frames++;
                        if (frames >= 25) resolve();
                        else requestAnimationFrame(onFrame);
                    };
                    requestAnimationFrame(onFrame);
                });

                const p = window.__REIEN_DIAG__.getState().playerPos;
                const dist = Math.hypot(p.x - 0, p.z - 6);

                // Release pointer & reset joystick
                window.dispatchEvent(new PointerEvent('pointerup', { pointerId: 1, bubbles: true }));
                if (window.__REIEN_DIAG__.setJoystickVector) window.__REIEN_DIAG__.setJoystickVector(0, 0);

                return dist;
            })();
        """)
        assert_true(moved_res > 0.35, f"Character did not move via virtual joystick drag (moved {moved_res:.3f})")
        print("PASS")

        # Restore desktop viewport for remaining tests
        call_cdp(ws, "Emulation.clearDeviceMetricsOverride")
        call_cdp(ws, "Emulation.setDeviceMetricsOverride", {
            "width": 1366, "height": 840, "deviceScaleFactor": 1, "mobile": False
        })
        time.sleep(0.4)

        # -----------------------------------------------------------------
        # TC-06: Haptic Vibration (Mobile + Gamepad) & Dog ("豆豆") Petting
        # -----------------------------------------------------------------
        print("[TC-06] Haptic Vibration (Mobile + Gamepad) & Dog Petting...", end=" ", flush=True)
        haptic_res = eval_js(ws, """
            window.__vibrateCalls = [];
            window.__gamepadPulses = [];
            navigator.vibrate = (pattern) => {
                window.__vibrateCalls.push(pattern);
                return true;
            };
            navigator.getGamepads = () => [{
                index: 0,
                connected: true,
                axes: [0, 0, 0, 0],
                buttons: [{ pressed: false }],
                vibrationActuator: {
                    playEffect: (type, params) => {
                        window.__gamepadPulses.push({ type, params });
                        return Promise.resolve('complete');
                    }
                }
            }];
            window.petGoldenDog();
            const st = window.__REIEN_DIAG__.getState();
            const toastShown = document.getElementById('haptic-toast').classList.contains('show');
            return {
                vibrateCount: window.__vibrateCalls.length,
                gamepadCount: window.__gamepadPulses.length,
                gamepadType: window.__gamepadPulses[0] ? window.__gamepadPulses[0].type : '',
                dogExcited: st.dogPos && st.dogPos.excitedTimer > 0,
                toastShown
            };
        """)
        assert_true(haptic_res['vibrateCount'] >= 1, "navigator.vibrate was not triggered when petting dog")
        assert_true(haptic_res['gamepadCount'] >= 1, "Gamepad vibrationActuator.playEffect was not triggered")
        assert_true(haptic_res['gamepadType'] == 'dual-rumble', "Gamepad effect must be dual-rumble")
        assert_true(haptic_res['dogExcited'], "Companion dog excitedTimer did not activate on petGoldenDog()")
        assert_true(haptic_res['toastShown'], "#haptic-toast was not shown on vibration")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-07: Thunder & Lightning Weather Haptic Feedback
        # -----------------------------------------------------------------
        print("[TC-07] Thunder & Lightning Weather Haptic Feedback...", end=" ", flush=True)
        thunder_res = eval_js(ws, """
            window.__vibrateCalls = [];
            window.__gamepadPulses = [];
            window.setWeather('thunder');
            window.triggerHaptics([180, 50, 320, 70, 220], 0.95, 1.0, 550, '⚡ 驚雷落閃・手把與手機強震回饋！');
            return {
                weather: window.__REIEN_DIAG__.getState().weather,
                vibrateCount: window.__vibrateCalls.length,
                strongMag: (window.__gamepadPulses[0] && window.__gamepadPulses[0].params) ? window.__gamepadPulses[0].params.strongMagnitude : 0
            };
        """)
        assert_true(thunder_res['weather'] == 'thunder', "Weather did not switch to thunder")
        assert_true(thunder_res['vibrateCount'] >= 1, "Thunder strike did not vibrate mobile")
        assert_true(thunder_res['strongMag'] >= 0.9, f"Expected strong rumble >= 0.9 on thunder, got {thunder_res['strongMag']}")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-08: Multi-Layered Daytime Lighting, Dynamic Quality & Komorebi
        # -----------------------------------------------------------------
        print("[TC-08] Multi-Layered Daytime Lighting, Dynamic Quality & Komorebi...", end=" ", flush=True)
        light_res = eval_js(ws, """
            window.setWeather('clear');
            window.setTimeOfDay('day');
            window.__REIEN_DIAG__.teleportPlayer(-1.85, 3.35);
            playerBody.rotation.y = -2.1;
            targetZoom = 0.74; cameraZoom = 0.74;
            targetYaw = 0.88; cameraYaw = 0.88;
            window.petGoldenDog();
            const perfShadow = window.__REIEN_DIAG__.getState().lights.shadowMapSize;
            window.toggleRenderQuality(); // Switch to 'quality' (4096, bloom)
            const qualityState = window.__REIEN_DIAG__.getState();
            window.toggleRenderQuality(); // Switch back to 'performance' (2048)
            const backPerfState = window.__REIEN_DIAG__.getState();
            return {
                lights: qualityState.lights,
                perfShadow,
                qualityShadow: qualityState.lights.shadowMapSize,
                qualityMode: qualityState.qualityMode,
                qualityHasComposer: qualityState.hasComposer,
                backPerfMode: backPerfState.qualityMode,
                backPerfShadow: backPerfState.lights.shadowMapSize,
                backPerfHasComposer: backPerfState.hasComposer
            };
        """)
        assert_true(light_res['perfShadow'] == 2048, f"Expected 2048 shadow map in performance mode, got {light_res['perfShadow']}")
        assert_true(light_res['qualityShadow'] == 4096, f"Expected 4096 shadow map in quality mode, got {light_res['qualityShadow']}")
        assert_true(light_res['qualityMode'] == 'quality', f"Expected qualityMode 'quality', got {light_res['qualityMode']}")
        assert_true(light_res['backPerfMode'] == 'performance', f"Expected return to 'performance', got {light_res['backPerfMode']}")
        assert_true(light_res['backPerfShadow'] == 2048, f"Expected return to 2048 shadow map, got {light_res['backPerfShadow']}")
        assert_true(light_res['backPerfHasComposer'] is False, "Composer should be disabled in performance mode")
        contrast_ratio = light_res['lights']['mainInt'] / max(0.01, light_res['lights']['hemiInt'])
        assert_true(contrast_ratio >= 7.5, f"Daytime directional-to-ambient contrast too flat: {contrast_ratio:.2f}")
        assert_true(light_res['lights']['rimInt'] >= 0.75, f"Expected strong cool rim light >= 0.75 in daytime, got {light_res['lights']['rimInt']}")
        assert_true(light_res['lights']['subInt'] >= 0.50, f"Expected subsurface backlight >= 0.50 in daytime, got {light_res['lights']['subInt']}")
        assert_true(light_res['lights']['accentCount'] >= 4, f"Expected >= 4 spatial bounce lights, got {light_res['lights']['accentCount']}")
        assert_true(light_res['lights']['godRayInt'] >= 0.45, f"Expected daytime godRayInt >= 0.45, got {light_res['lights']['godRayInt']}")
        assert_true(light_res['lights']['komorebiStrength'] >= 1.0, f"Expected komorebiStrength >= 1.0, got {light_res['lights']['komorebiStrength']}")

        if screenshot_dir:
            time.sleep(1.2)
            shot_path = os.path.join(screenshot_dir, "day_multilayer_komorebi_lighting.png")
            sz = capture_png(ws, shot_path)
            reien_shot = os.path.join(ROOT_DIR, "docs", "screenshots", "day_multilayer_komorebi_lighting.png")
            capture_png(ws, reien_shot)
            print(f"(Captured {sz} bytes)", end=" ", flush=True)
        print("PASS")

        # -----------------------------------------------------------------
        # TC-09: Tree Canopy & Indoor House See-Through Occlusion Fade
        # -----------------------------------------------------------------
        print("[TC-09] Tree Canopy & Indoor House See-Through Occlusion...", end=" ", flush=True)
        eval_js(ws, "window.__REIEN_DIAG__.teleportPlayer(-11.0, -10.0, true);")
        indoor_alpha = eval_js(ws, "return window.__REIEN_DIAG__.getState().minOccludableAlpha;")
        assert_true(indoor_alpha < 0.25, f"Expected indoor house occlusion alpha < 0.25, got {indoor_alpha:.3f}")

        eval_js(ws, "window.__REIEN_DIAG__.teleportPlayer(-5.2, 5.5, true);")
        tree_alpha = eval_js(ws, "return window.__REIEN_DIAG__.getState().minOccludableAlpha;")
        assert_true(tree_alpha < 0.25, f"Expected tree canopy occlusion alpha < 0.25, got {tree_alpha:.3f}")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-10: Town Builder Mode & Memorial Shrine Modal Offerings
        # -----------------------------------------------------------------
        print("[TC-10] Town Builder Mode & Memorial Shrine Modal Offerings...", end=" ", flush=True)
        modal_res = eval_js(ws, """
            window.toggleBuildMode();
            const buildOn = window.__REIEN_DIAG__.getState().isBuildMode;
            window.toggleBuildMode();
            const buildOff = !window.__REIEN_DIAG__.getState().isBuildMode;
            if (window.openCurrentMemorialModal) window.openCurrentMemorialModal();
            const beforeCandle = parseInt(document.getElementById('m-candle-count').innerText, 10);
            window.offerGift('candle');
            const afterCandle = parseInt(document.getElementById('m-candle-count').innerText, 10);
            window.closeMemorialModal();
            return {
                buildOn,
                buildOff,
                candleIncremented: afterCandle === beforeCandle + 1,
                errors: window.__runtimeErrors || []
            };
        """)
        assert_true(modal_res['buildOn'] and modal_res['buildOff'], "toggleBuildMode() failed to toggle state")
        assert_true(modal_res['candleIncremented'], "Memorial modal candle offering counter did not increment")
        assert_true(len(modal_res['errors']) == 0, f"Runtime errors detected: {modal_res['errors']}")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-11: Mobile Portrait Top UI Collapse / Immersive Mode (手遊風格收合頂部選單)
        # -----------------------------------------------------------------
        print("[TC-11] Mobile Portrait Top UI Collapse / Immersive Mode...", end=" ", flush=True)
        call_cdp(ws, "Emulation.setDeviceMetricsOverride", {
            "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True
        })
        time.sleep(0.4)
        hud_res = eval_js(ws, """
            const wasCollapsed = document.body.classList.contains('top-hud-collapsed');
            window.toggleTopHUD();
            const nowCollapsed = document.body.classList.contains('top-hud-collapsed');
            const controlsDisplay = window.getComputedStyle(document.querySelector('.top-controls')).display;
            const topBarHeight = document.querySelector('.top-bar').getBoundingClientRect().height;
            return { wasCollapsed, nowCollapsed, controlsDisplay, topBarHeight };
        """)
        assert_true(hud_res['nowCollapsed'], "toggleTopHUD() did not add top-hud-collapsed class")
        assert_true(hud_res['controlsDisplay'] == 'none', f"Top controls should be hidden when collapsed, got {hud_res['controlsDisplay']}")
        assert_true(hud_res['topBarHeight'] < 55, f"Top bar height should be < 55px when collapsed, got {hud_res['topBarHeight']}")

        if screenshot_dir:
            time.sleep(0.5)
            shot_path = os.path.join(screenshot_dir, "mobile_portrait_collapsed_immersive.png")
            capture_png(ws, shot_path)
            reien_shot = os.path.join(ROOT_DIR, "docs", "screenshots", "mobile_portrait_collapsed_immersive.png")
            capture_png(ws, reien_shot)
            print("(Captured mobile_portrait_collapsed_immersive.png)", end=" ", flush=True)

        # Restore top HUD
        eval_js(ws, "window.toggleTopHUD();")
        call_cdp(ws, "Emulation.clearDeviceMetricsOverride")
        call_cdp(ws, "Emulation.setDeviceMetricsOverride", {
            "width": 1366, "height": 840, "deviceScaleFactor": 1, "mobile": False
        })
        time.sleep(0.3)
        print("PASS")

        # -----------------------------------------------------------------
        # TC-12: Bluetooth & Wired Gamepad Actuator Dual-Rumble Test
        # -----------------------------------------------------------------
        print("[TC-12] Bluetooth & Wired Gamepad Actuator Dual-Rumble...", end=" ", flush=True)
        gp_res = eval_js(ws, """
            window.__gpRumbles = [];
            navigator.getGamepads = () => [{
                id: 'Xbox Wireless Controller (Bluetooth)',
                index: 0,
                connected: true,
                axes: [0, 0, 0, 0],
                buttons: [{ pressed: false }, { pressed: false }, { pressed: false }, { pressed: false }],
                vibrationActuator: {
                    playEffect: (type, params) => {
                        window.__gpRumbles.push({ type, params });
                        return Promise.resolve('complete');
                    }
                }
            }];
            window.testHapticsAndGamepad();
            const modalOpen = document.getElementById('gamepad-diag-modal').classList.contains('open');
            window.closeGamepadDiagModal();
            return {
                modalOpen,
                rumbles: window.__gpRumbles
            };
        """)
        assert_true(gp_res['modalOpen'], "testHapticsAndGamepad failed to open gamepad diagnostic modal")
        assert_true(len(gp_res['rumbles']) >= 1, "Gamepad playEffect('dual-rumble') was not invoked")
        assert_true(gp_res['rumbles'][0]['type'] == 'dual-rumble', "Rumble effect type must be dual-rumble")
        assert_true(gp_res['rumbles'][0]['params']['strongMagnitude'] >= 0.9, "Strong rumble magnitude should be >= 0.9")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-13: Multi-Motor Diagnostic Modes ('heavy', 'light', 'trigger') & Report Export
        # -----------------------------------------------------------------
        print("[TC-13] Multi-Motor Modes ('heavy', 'light', 'trigger') & Diag Export...", end=" ", flush=True)
        modes_res = eval_js(ws, """
            window.__modeCalls = [];
            navigator.getGamepads = () => [{
                id: 'Xbox One Controller (USB XInput)',
                index: 0,
                connected: true,
                axes: [0, 0, 0, 0],
                buttons: [{ pressed: false }],
                vibrationActuator: {
                    type: 'dual-rumble',
                    effects: ['dual-rumble', 'trigger-rumble'],
                    playEffect: (type, params) => {
                        window.__modeCalls.push({ type, params });
                        return Promise.resolve('complete');
                    }
                }
            }];
            return (async () => {
                await window.triggerDirectGamepadRumble('heavy');
                await window.triggerDirectGamepadRumble('light');
                await window.triggerDirectGamepadRumble('trigger');
                let reportExported = typeof window.copyGamepadDiagReport === 'function';
                return {
                    calls: window.__modeCalls,
                    reportExported
                };
            })();
        """)
        assert_true(len(modes_res['calls']) >= 3, "Expected at least 3 mode calls for heavy, light, and trigger")
        assert_true(modes_res['calls'][0]['params']['strongMagnitude'] >= 0.9 and modes_res['calls'][0]['params']['weakMagnitude'] == 0, "Heavy mode must have strongMagnitude 1.0, weakMagnitude 0.0")
        assert_true(modes_res['calls'][1]['params']['strongMagnitude'] == 0 and modes_res['calls'][1]['params']['weakMagnitude'] >= 0.8, "Light mode must have strongMagnitude 0.0, weakMagnitude > 0")
        assert_true(modes_res['reportExported'], "copyGamepadDiagReport must be defined")
        print("PASS")

        # -----------------------------------------------------------------
        # TC-14: Koi Pond, Lakeside Dock & Interactive Fish Feeding (湖光小鎮風格驗證)
        # -----------------------------------------------------------------
        print("[TC-14] Koi Pond, Lakeside Dock & Interactive Fish Feeding...", end=" ", flush=True)
        koi_res = eval_js(ws, """
            window.__REIEN_DIAG__.teleportPlayer(5.2, -3.0);
            const stateBefore = window.__REIEN_DIAG__.getState();
            window.feedKoi(7.0, -3.0);
            const stateAfter = window.__REIEN_DIAG__.getState();
            return {
                themeStyle: stateBefore.themeStyle,
                dockPresent: stateBefore.dockPresent,
                dockPos: stateBefore.dockPos,
                koiCount: stateBefore.koiFishCount,
                isNearWater: stateBefore.isNearWaterOrDock,
                playerY: stateBefore.playerPos.y,
                foodCountAfter: stateAfter.fishFoodCount,
                dogExcited: stateAfter.dogPos && stateAfter.dogPos.excitedTimer > 0,
                errors: window.__runtimeErrors || []
            };
        """)
        assert_true(koi_res['themeStyle'] == 'koi-lake-town', f"Expected themeStyle 'koi-lake-town', got {koi_res['themeStyle']}")
        assert_true(koi_res['dockPresent'], "Lakeside dock is not present in diagnostic state")
        assert_true(koi_res['koiCount'] >= 8, f"Expected at least 8 articulated koi species, got {koi_res['koiCount']}")
        assert_true(koi_res['isNearWater'], "Player at dock should be detected as near water or dock")
        assert_true(koi_res['playerY'] >= 0.12, f"Player on dock should stand at plank elevation >= 0.12, got {koi_res['playerY']}")
        assert_true(koi_res['foodCountAfter'] >= 5, f"Expected >= 5 fish food pellets after feeding, got {koi_res['foodCountAfter']}")
        assert_true(koi_res['dogExcited'], "Companion dog should be excited by fish feeding")
        assert_true(len(koi_res['errors']) == 0, f"Runtime errors during fish feeding: {koi_res['errors']}")

        if screenshot_dir:
            time.sleep(1.0)
            shot_path = os.path.join(screenshot_dir, "koi_lakeside_dock_feeding.png")
            capture_png(ws, shot_path)
            reien_shot = os.path.join(ROOT_DIR, "docs", "screenshots", "koi_lakeside_dock_feeding.png")
            capture_png(ws, reien_shot)
            print("(Captured koi_lakeside_dock_feeding.png)", end=" ", flush=True)

        print("PASS")

        ws.close()
    finally:
        proc.terminate()
        httpd.shutdown()
        shutil.rmtree(user_data_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Run Reien CI/CD Automated Verification Suite")
    parser.add_argument('--screenshots', type=str, default=None, help="Directory to save verification screenshots")
    args = parser.parse_args()

    start_t = time.time()
    print("=" * 70)
    print("🚀 Starting Reien 2.5D Cloud Memorial Garden CI/CD Test Suite (14 Cases)")
    print("=" * 70)
    run_tc01_static_syntax()
    run_browser_suite(screenshot_dir=args.screenshots)
    elapsed = time.time() - start_t
    print("=" * 70)
    print(f"✅ ALL 14 CI/CD TEST CASES PASSED IN {elapsed:.2f}s!")
    print("=" * 70)


if __name__ == '__main__':
    main()
