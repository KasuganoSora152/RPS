# RPsoft

一个**完全本地**的角色扮演 / AI 对话应用，以**桌面软件窗口**运行：接入 DeepSeek API，支持自定义角色卡，轻量化、纯 JSON 存储，无数据库、无前端构建步骤。

## 目录结构

```
RPsoft/
├── RPsoft.exe            # 打包后的启动器（运行 build.bat 生成）
├── code/                 # 全部代码
│   ├── run.py            # 启动入口
│   └── app/              # FastAPI 应用（api / core / models / web）
├── data/                 # 全部数据（角色卡、聊天记录、配置）
│   ├── characters/       # 角色卡（.json）
│   ├── chats/            # 聊天记录（自动生成）
│   └── config.json       # 配置（含 API Key，首次运行自动生成）
└── others/               # 其他文件（文档、依赖、打包脚本）
    ├── README.md
    ├── requirements.txt
    ├── RPsoft.spec       # PyInstaller 打包配置
    └── build.bat         # 一键打包脚本
```

## 角色卡格式

角色卡就是一个 JSON 文件，字段如下（全部可选）：

```json
{
  "name": "角色名",
  "description": "描述",
  "personality": "性格",
  "scenario": "背景 / 世界观",
  "greeting": "开场白（第一条消息）",
  "dialogue_examples": "对话示例",
  "system_prompt": "额外设定",
  "tags": ["标签1", "标签2"]
}
```

## 快速开始

> 需要 Python 3.10+（推荐 3.11+）。项目已在 Python 3.14 上验证。

```powershell
cd D:\dsh\dsh_workspace\RPsoft
py -m venv others\.venv
others\.venv\Scripts\Activate.ps1
pip install -r others\requirements.txt
python code\run.py
```

启动后会打开一个**原生桌面窗口**（基于 Windows 自带的 WebView2，无需安装浏览器）。首次使用请点击右上角「⚙ 设置」，填入 [DeepSeek API Key](https://platform.deepseek.com/) 并「测试连接」。

> 配置模板：仓库里的 `data/config.example.json` 是一份**不含密钥**的配置模板，可复制为 `data/config.json` 并填入 API Key（应用在首次保存设置时也会自动生成 `config.json`）。

其他启动方式：

- `python code\run.py --browser`：改用浏览器打开
- `python code\run.py --serve-only`：只启动服务、不弹界面（调试用）
- `python code\run.py --port 9000`：改端口

> 若系统缺少 WebView2 运行时（个别旧 Win10），程序会自动回退到浏览器打开。

## 使用说明

1. 「新建角色」创建一个角色（填好名称、描述、性格、开场白等）
2. 左侧「角色」点击任意角色 → 自动开新对话（角色开场白会成为第一条回复）
3. 底部输入消息，`Enter` 发送、`Shift+Enter` 换行
4. 「导入角色卡」可导入 `.json` 角色卡（格式见上）
5. 系统提示词模板支持占位符：`{name}` `{description}` `{personality}` `{scenario}` `{dialogue_examples}` `{system_prompt}`

## 默认接口配置

| 配置项 | 默认值 |
| --- | --- |
| Base URL | `https://api.deepseek.com/v1` |
| 模型 | `deepseek-v4-flash`（对话）或 `deepseek-v4-pro`（推理） |
| Temperature | `1.0` |
| Max Tokens | `2048` |

## 打包成 Windows 启动器（exe）

本机已装 Python 3.10+ 即可。双击 `others\build.bat`，或在项目根目录执行：

```powershell
py -m venv others\.venv
others\.venv\Scripts\Activate.ps1
pip install -r others\requirements.txt pyinstaller
pyinstaller --clean --noconfirm --distpath . --workpath others\build others\RPsoft.spec
```

产物为项目根目录下的 **`RPsoft.exe`**（onefile 单文件、无控制台窗口，双击即打开软件窗口；无需安装 Python、无需附带其它文件即可运行；用户数据仍写入同级的 `data\` 文件夹）。

说明：

- 采用 **onefile** 模式（单文件 exe），目录最简洁；代价是每次启动需解包到临时目录，比 onedir 稍慢 1~3 秒。
- 用户数据（角色卡、聊天记录、`config.json`）保存在 `data\`，随 `RPsoft.exe` 一起备份即可。

## 后续规划

- [ ] 多轮上下文上限 / 摘要压缩
- [ ] 会话导出 / 导入
- [ ] 更多模型参数（thinking、top_k 等）暴露到设置
- [x] PyInstaller 封装为免安装单文件 exe（已完成：见上）
