"""启动入口：本地服务器 + 原生桌面窗口。

默认打开一个原生窗口加载界面（pywebview / WebView2），关窗即退出；
--browser 改用浏览器，--serve-only 只启动服务不弹界面（调试用）。
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import webbrowser

import uvicorn

from app.config import ensure_dirs, load_config
from app.main import app

# 无控制台（windowed）运行时，把 stdout/stderr 指向空设备，避免 print/logging 崩溃
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = sys.stdout


def _show_error(message: str) -> None:
    """窗口化运行时弹出错误提示框（无控制台时也能看到报错）。"""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "RPS~测试版", 0x10)  # MB_ICONERROR
    except Exception:
        pass


def _start_server(host: str, port: int) -> tuple[uvicorn.Server, threading.Thread]:
    """在后台线程启动 uvicorn，等待就绪后返回 (Server, 线程)。"""
    server = uvicorn.Server(
        uvicorn.Config(app, host=host, port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):  # 最多等 10 秒
        if server.started:
            return server, thread
        if not thread.is_alive():
            raise RuntimeError("服务器启动失败（端口可能被占用）")
        time.sleep(0.1)
    raise RuntimeError("服务器启动超时")


def _wait_forever() -> None:
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


def _run_browser_mode(url: str) -> None:
    webbrowser.open(url)
    print(f"已在浏览器打开：{url}（按 Ctrl+C 退出）")
    _wait_forever()


def _run_window_mode(url: str) -> None:
    import webview

    webview.create_window("RPS~测试版", url, width=1100, height=760, min_size=(820, 580))
    webview.start()


def main() -> None:
    ensure_dirs()
    cfg = load_config()

    parser = argparse.ArgumentParser(description="RPsoft 本地启动器")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=cfg.get("port", 8000))
    parser.add_argument("--browser", action="store_true", help="用浏览器打开，而不是内置窗口")
    parser.add_argument("--serve-only", action="store_true", help="只启动服务，不打开任何界面（调试用）")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"

    try:
        server, server_thread = _start_server(args.host, args.port)
    except Exception as exc:  # noqa: BLE001
        _show_error(f"RPsoft 启动失败：{exc}")
        return

    try:
        if args.serve_only:
            print(f"服务已启动：{url}（按 Ctrl+C 退出）")
            _wait_forever()
        elif args.browser:
            _run_browser_mode(url)
        else:
            try:
                _run_window_mode(url)
            except Exception as exc:  # WebView2 缺失等情况，回退到浏览器
                print(f"无法打开内置窗口（{exc}），改用浏览器打开。")
                _run_browser_mode(url)
    finally:
        # 优雅关停服务器；pythonnet/.NET 会残留非守护线程导致进程不退出，
        # 必须用 os._exit 兜底，保证端口立即释放、可马上重新打开。
        server.should_exit = True
        server_thread.join(timeout=2)
        os._exit(0)


if __name__ == "__main__":
    main()
