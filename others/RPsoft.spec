# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（onefile 模式，产出单个 RPsoft.exe 到项目根目录）。

在项目根目录执行（build.bat 会自动 cd 到根目录）：
    pyinstaller --clean --noconfirm --distpath . --workpath others/build others/RPsoft.spec
"""
import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

ROOT = os.path.abspath(".")  # 项目根目录

datas = [
    (os.path.join(ROOT, "code", "app", "web"), "app/web"),  # 前端静态资源
]
datas += collect_data_files("certifi")  # httpx 校验 HTTPS 所需的 CA 证书

binaries = []
hiddenimports = [
    # uvicorn 存在动态导入，显式声明避免打包遗漏
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]

# pywebview 及其依赖（pythonnet / clr）的隐藏导入、数据与二进制
for pkg in ("webview", "pythonnet", "clr", "clr_loader"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [os.path.join(ROOT, "code", "run.py")],
    pathex=[os.path.join(ROOT, "code")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RPsoft",
    icon=os.path.join(ROOT, "others", "RPS_icon_multi.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无控制台窗口：以纯桌面软件窗口运行
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="RPsoft",
)
