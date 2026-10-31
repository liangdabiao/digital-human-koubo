# 安装引导（只在缺的时候用）

原则：**已经有的一句话带过，不提安装**；缺什么才给装法。装法给多种：先放用户当前在用的那种（标「推荐」），其余列在下面让用户挑。装完再检查一次确认。装好后跑 `bash scripts/doctor.sh` 核验。

## 1. dreamina CLI（即梦官方，生成主力）

### 怎么判断有没有
终端跑 `dreamina user_credit`：
- 返回积分数字 → 「即梦已登录，余额 X 积分」，继续干活。
- 报找不到命令 → 没装，按下面装。
- 报未登录 → 不用重装，`dreamina login` 重新授权就行。

### 装法（官方安装器，装完自动加 PATH）
```bash
curl -s https://jimeng.jianying.com/cli | bash
```
装完重开终端（或 `export PATH="$HOME/bin:$PATH"`），然后登录：
- **推荐**：`dreamina login` —— 浏览器打开它给的 verification_uri，输入 user_code 授权即可（OAuth 设备码，不用复制任何 key）
- 无浏览器环境：`dreamina login --headless` 拿到设备码 → 任意浏览器打开链接授权 → `dreamina login checklogin --device_code=<device_code>`

账户说明：即梦积分每日可领；`seedance2.0mini` 是日常主力（实测 6 积分/秒、0 排队）；`seedance2.5` 最长 30 秒、VIP 专属。**不要用 seedance2.0fast**——晚高峰队列会排几小时。

## 2. apiz CLI（台词核验 / TTS / 克隆声 / 备用生成）

### 怎么判断有没有
`apiz account balance` 返回余额 → 已就绪（用于 align QC：核验台词 + 出字级时间轴，10 积分/段）。

### 装法
```bash
curl -fsSL https://data.apiz.ai/cli/install.sh | bash     # 或见 apiz.ai 官网安装文档
apiz auth login                                            # 存 API key（sk-…）
```

## 3. 本机环境
`bash scripts/doctor.sh` 逐项检查：有的打 ✓ 跳过，缺的才列装法。**系统软件让用户自己装，不要替用户执行安装命令**（Python 包可以在用户同意后帮装）。

| 缺的 | macOS | Windows | Linux | 说明 |
|---|---|---|---|---|
| ffmpeg | `brew install ffmpeg` | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` | 抽帧/拼接/响度 |
| Python 3 | `brew install python` | `winget install Python.Python.3.12` | `sudo apt install python3 python3-pip` | 全部流程脚本 |
| numpy / Pillow | `python3 -m pip install numpy pillow` | 同左 | 同左 | 声音统一 / 预览图 |
| Node 18+ | `brew install node` | `winget install OpenJS.NodeJS.LTS` | nvm / apt | Remotion 剪辑 |
| edge-tts（可选） | `pip install edge-tts` | 同左 | 同左 | 只有旁白段/指定音色才需要 |
| whisper.cpp（可选） | `brew install whisper-cpp` + 模型放 `~/models/` | Releases 下载 | 源码编译 | 默认 QC 走 apiz align；想零积分回听再装 |

Remotion 不用单独装：`scripts/new_edit.sh` 起工程时会先从本机已有的 Remotion 工程克隆，没有才 `npm install`；npm 源连不上时换镜像 `npm config set registry https://registry.npmmirror.com`。

## 4. 数字人形象
persona.json → `media.reference_image` 指向本地参考图（默认 `assets/avatar_ref.jpg`，仓库自带）。要换成用户自己的形象：把照片放进来改路径即可；要做全新四视图形象 → 按 references/new-avatar.md。**不要填即梦网页的素材 ID，CLI 只吃本地文件。**
