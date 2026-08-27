<table align="center">
  <tr>
    <td><img src="others/RPS_icon-256.png" alt="RPsoft" width="88"></td>
    <td><h1>RPsoft</h1></td>
  </tr>
</table>

一个**完全本地**的角色扮演 / AI 对话桌面应用：接入 DeepSeek API，支持自定义角色卡，轻量化、纯 JSON 存储——无数据库、无前端构建步骤，双击 exe 即用。

## 特性

- **原生桌面窗口**：基于 Windows 自带的 WebView2 运行，无需安装浏览器（个别旧 Win10 会自动回退到系统浏览器打开）
- **DeepSeek API**：支持 `deepseek-v4-flash`（对话）与 `deepseek-v4-pro`（推理）两种模型
- **自定义角色卡**：纯 JSON 格式，可新建、导入
- **轻量存储**：角色、聊天记录、配置均为本地 JSON 文件，零依赖数据库
- **流式输出**：回复以 SSE 流式返回，逐字呈现
- **明暗主题**：浅色 / 深色一键切换，偏好自动保存

## 目录结构

```
RPsoft/
├── .gitignore            # Git 忽略规则（排除密钥、聊天记录、构建产物）
├── README.md             # 本文档
├── LICENSE               # GPL-3.0 许可证
├── RPsoft.exe            # 打包后的启动器（运行 build.bat 生成，已 git 忽略）
├── _internal/            # 打包运行时（onedir 产物，与 exe 配套，勿删）
├── code/                 # 全部代码
│   ├── run.py            # 启动入口
│   └── app/              # FastAPI 应用（api / core / models / web）
├── data/                 # 全部数据（角色卡、聊天记录、配置）
│   ├── characters/       # 角色卡（.json）
│   ├── chats/            # 聊天记录（自动生成，已 git 忽略）
│   ├── config.json       # 配置（含 API Key，首次运行自动生成，已 git 忽略）
│   └── config.example.json  # 配置模板（不含密钥，可直接复制使用）
└── others/               # 其他文件（依赖、打包脚本、图标）
    ├── requirements.txt  # Python 依赖
    ├── RPsoft.spec       # PyInstaller 打包配置（onedir）
    └── build.bat         # 一键打包脚本
```

## 快速开始

> 需要 Python 3.10+（推荐 3.11+）。项目已在 Python 3.14 上验证。

```powershell
cd RPsoft
py -m venv others\.venv
others\.venv\Scripts\Activate.ps1
pip install -r others\requirements.txt
python code\run.py
```

启动后会打开一个**原生桌面窗口**。首次使用请点击右上角「⚙ 设置」，填入 [DeepSeek API Key](https://platform.deepseek.com/) 并「测试连接」。

> 配置模板：仓库里的 `data/config.example.json` 是一份**不含密钥**的配置模板，可复制为 `data/config.json` 并填入 API Key（应用在首次保存设置时也会自动生成 `config.json`）。

其他启动方式：

| 参数 | 作用 |
| --- | --- |
| `--browser` | 改用系统浏览器打开 |
| `--serve-only` | 只启动服务、不弹界面（调试用） |
| `--port 9000` | 指定端口 |

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
| 模型 | `deepseek-v4-flash`（对话）/ `deepseek-v4-pro`（推理） |
| Temperature | `1.0` |
| Max Tokens | `2048` |
| 主题 | 浅色（可在设置中切换深色） |

## 打包成 Windows 启动器（exe）

本机装好 Python 3.10+ 即可。双击 `others\build.bat`，或在项目根目录执行：

```powershell
py -m venv others\.venv
others\.venv\Scripts\Activate.ps1
pip install -r others\requirements.txt pyinstaller
pyinstaller --clean --noconfirm --distpath . --workpath others\build others\RPsoft.spec
```

产物为项目根目录下的 **`RPsoft.exe`** + **`_internal\`** 文件夹（**onedir** 模式、无控制台窗口）。双击 `RPsoft.exe` 即打开软件窗口，无需安装 Python、无需配置环境。

说明：

- 采用 **onedir** 模式：`RPsoft.exe` 与 `_internal\` 必须**保持在一起**（`_internal\` 内含 Python 运行时与依赖，删除后无法启动）。
- 相比 onefile 单文件，onedir 启动更快（无需每次解包到临时目录）；代价是根目录多一个 `_internal\` 文件夹。
- 用户数据（角色卡、聊天记录、`config.json`）保存在 `data\`，随 `RPsoft.exe` 一起备份即可。
- `RPsoft.exe` 与 `_internal\` 均已被 `.gitignore` 忽略，不会进入版本库。

## 许可证

本项目采用 [GNU General Public License v3.0（GPL-3.0）](LICENSE)。简而言之：你可以自由使用、修改、分发本项目，但衍生作品也必须以 GPL-3.0 开源。完整条款见仓库根目录的 [`LICENSE`](LICENSE) 文件。

## 后续规划

- [ ] 多轮上下文上限 / 摘要压缩
- [ ] 会话导出 / 导入
- [ ] 更多模型参数（thinking、top_k 等）暴露到设置
- [x] PyInstaller 封装为免安装 exe（已完成：onedir 模式）
