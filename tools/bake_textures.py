# -*- coding: utf-8 -*-
"""
Offline texture baker for Reien.

Runs the procedural Canvas2D texture generators in a headless Chrome once and
writes the results as static WebP files under assets/textures/. index.html then
loads those files asynchronously, so the main thread no longer performs
per-pixel normal-map maths during startup.

Usage:
    python3 tools/bake_textures.py

Requires a local Chrome/Chromium/Edge (same discovery as tests/e2e_ci_suite.py).
"""
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TESTS_DIR = os.path.join(ROOT_DIR, 'tests')
OUT_DIR = os.path.join(ROOT_DIR, 'assets', 'textures')
BAKE_PAGE = 'tools/texture_bake/bake.html'

sys.path.insert(0, TESTS_DIR)
from e2e_ci_suite import (  # noqa: E402
    RobustWSClient,
    find_browser_binary,
    start_background_server,
)

EXPECTED = [
    ('cobblestone_albedo', 256, 256),
    ('cobblestone_normal', 256, 256),
    ('cobblestone_roughness', 256, 256),
    ('grass_albedo', 256, 256),
    ('grass_normal', 256, 256),
    ('bark_albedo', 256, 256),
    ('bark_normal', 256, 256),
    ('sakura_sprig', 512, 512),
    ('pine_branch', 256, 256),
]


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def wait_for_cdp(proc, port, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f'Headless browser exited prematurely (code {proc.returncode})')
        try:
            raw = urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=1).read()
            tabs = json.loads(raw)
            page = next((t for t in tabs if t.get('type') == 'page'), None)
            if page:
                return page
        except Exception:
            pass
        time.sleep(0.25)
    raise TimeoutError('Timed out waiting for Chrome DevTools endpoint')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    httpd, http_port = start_background_server(ROOT_DIR)
    browser_bin = find_browser_binary()
    debug_port = free_port()
    user_data_dir = tempfile.mkdtemp(prefix='reien_texture_bake_')

    cmd = [
        browser_bin,
        '--headless=new',
        f'--remote-debugging-port={debug_port}',
        f'--user-data-dir={user_data_dir}',
        '--window-size=800,600',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        'about:blank',
    ]
    if sys.platform.startswith('linux'):
        cmd[1:1] = ['--no-sandbox', '--disable-gpu-sandbox']

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        page = wait_for_cdp(proc, debug_port)
        ws = RobustWSClient(page['webSocketDebuggerUrl'])
        try:
            try:
                ws.call_cdp('Page.enable', timeout=5)
            except Exception:
                pass

            url = f'http://127.0.0.1:{http_port}/{BAKE_PAGE}'
            print(f'[bake] Loading {url}')
            ws.call_cdp('Page.navigate', {'url': url}, timeout=15)

            ready = False
            for _ in range(80):
                try:
                    state = ws.eval_js("return document.readyState + ':' + (typeof window.__BAKE_TEXTURES__);", timeout=2)
                    if state == 'complete:function':
                        ready = True
                        break
                except Exception:
                    pass
                time.sleep(0.25)
            if not ready:
                raise RuntimeError('Bake page did not become ready')

            print('[bake] Generating procedural canvases (this is the offline cost we are removing)…')
            started = time.time()
            result = ws.eval_js('return window.__BAKE_TEXTURES__();', timeout=120)
            elapsed = time.time() - started
            print(f'[bake] Canvas generation finished in {elapsed:.2f}s')

            total_bytes = 0
            written = []
            for key, width, height in EXPECTED:
                item = result.get(key)
                if not item or 'dataUrl' not in item:
                    raise RuntimeError(f'Missing baked texture: {key}')
                if item['width'] != width or item['height'] != height:
                    raise RuntimeError(
                        f'Unexpected size for {key}: {item["width"]}x{item["height"]} (expected {width}x{height})'
                    )
                raw = base64.b64decode(item['dataUrl'].split(',', 1)[1])
                if len(raw) < 256 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
                    raise RuntimeError(f'Invalid WebP payload for {key} ({len(raw)} bytes)')
                path = os.path.join(OUT_DIR, key + '.webp')
                with open(path, 'wb') as f:
                    f.write(raw)
                total_bytes += len(raw)
                written.append((key, len(raw), width, height))

            print('[bake] Wrote:')
            for key, size, width, height in written:
                print(f'  - assets/textures/{key}.webp  {width}x{height}  {size / 1024:.1f} KiB')
            print(f'[bake] Total {total_bytes / 1024:.1f} KiB')
        finally:
            ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        httpd.shutdown()
        shutil.rmtree(user_data_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
