# 改造方案：digital-human-koubo → apiz CLI + 即梦 CLI + edge-tts 版

> 深度研究结论 · 2026-10-27 · 基于本机实测（apiz 已登录、余额 791.99 积分；edge-tts 7.3.1 可用；jimeng-cli 未装但已验证 npm 包与源码）

---

## 一、原版架构盘点

原版流程（Renoise 通道）：

```
写稿 script.json（≤15s/段）
  → build_tasks.py（Renoise Grok Video 1.5 任务，视频+配音一体生成）
  → Renoise MCP create_tasks / wait_tasks / download_results
  → rangedl.py 分片下载
  → assemble.py（whisper 回听 QC + 裁剪 + 拼接 + loudnorm）
  → align.py（whisper 逐字时间轴 → tl.json）
  → Remotion 剪辑（huazi-916 等 5 风格 + 48 包装组件）→ 渲染出片
```

**强依赖**：Renoise MCP（视频生成+原生配音，720p 17 积分/秒）、whisper.cpp + 1.5GB 模型（回听与打轴）、GPT Image 2.5（场景图，23 积分/张）、macOS Vision（景深字抠像）。

**改造要点**：把「视频生成时模型自己配音」换成「**TTS 前置 → 音频驱动口型**」，生成通道换成即梦（免费积分池）+ apiz（付费备份），whisper 从必需降级为可选抽查。

---

## 二、三个新工具的研究结论（本机实测）

### 2.1 edge-tts（已装 7.3.1，免费）

| 能力 | 实测结果 |
|---|---|
| 中文音色 | zh-CN-Xiaoxiao（温暖女声）、Xiaoyi（活泼）、Yunjian（激情男）、Yunxi（阳光男）、Yunyang（新闻男）+ 方言 + 粤语/台湾等 300+ 音色 |
| 多语言 | `en-US-EmmaMultilingualNeural` 等多语神经音色；每语言独立音色齐全 |
| 字级时间戳 | python API `SubMaker` + WordBoundary 事件 → **逐词毫秒偏移**，可零成本生成 tl.json |
| 输出 | mp3 音频 + SRT 字幕（`--write-subtitles`），实测一段 4.37s 正常产出 |
| 局限 | 情感表现力弱于 Minimax/Grok 原生配音；偶发服务波动需重试 |

### 2.2 apiz CLI（已装已登录，apiz.ai 平台）

| 命令 | 说明 | 花费 |
|---|---|---|
| `apiz generate` | 图片/视频生成，`--model` / `--image-url` / `--params '{...}'` / `--wait`；产物在 `data.output.media[].url` | 按模型 |
| `apiz models list/info` | 模型目录 | 免费 |
| `apiz upload` | 本地文件 → 公网 URL（TOS/CDN），音频参考必经之路 | 免费 |
| `apiz align` | 语音+已知文稿 → **字级毫秒时间戳**（火山 ata-speech 后端） | ≈10 积分/次 |
| `apiz speak` | Minimax speech-2.8-hd/turbo TTS，`--voice`/`--speed` | 少量 |
| `apiz voices list` / `voice-clone` / `voice-design` | 预置音色 / 克隆（10s+ 样本）/ 文字设计音色 | 少量 |
| `apiz account balance/checkin` | 余额 / 每日签到领分 | 免费 |

**关键模型发现**：
- **`st-ai/super-seed2`（Seedance 2.0 全能）**：官方描述明确「全能模式支持图片/视频/音频多模态混合输入（**最多 9 图 + 3 视频 + 3 音频**），`@image_file_N` 语法精确控制每个素材，**原生音画同步、音素级口型同步（8+ 种语言）**，4–15 秒」→ **音频驱动数字人口型的主力通道**。
- `apiz/seedance-2.5`：4–30 秒，480p/720p/1080p，同样支持「图片、视频、音频参考」（长段口播用）。
- `minimax/h3`：4–15 秒，图片/视频/音频混合参考（备份）。
- `volcengine/vod/subtitle-erase`：**擦字幕**工具——Seedance 偶尔烧字幕时的修复手段（原版 Grok 同款坑）。
- 图像：`apiz/gpt-image-2.5-flare`（场景合成）、`fal-ai/nano-banana-pro`、`apiz/seedream-5.0-pro`。

**价格警报**：apiz 的 Seedance 通道实测较贵（super-seed2-lite 720p ≈50 积分/秒，bytedance 通道 480p 43–54 积分/秒，2026-09 实测）——**约为原 Renoise Grok（17 积分/秒）的 3–6 倍**。因此 apiz 只做备份/精修通道，**零成本主力是即梦**。

### 2.3 jimeng-cli（npm `jimeng-cli@0.3.9`，GPL-3.0，未装）

即梦/CapCut 官方平台的非官方 CLI 封装，走 **mweb 网页 API + sessionid token 池**：

- 安装：`npm install -g jimeng-cli` → `jimeng login`（浏览器复制即梦 sessionid）
- **token 池**：多区域（cn/us/hk/jp/sg）多 token 轮换、健康检查、自动禁用；`jimeng token receive` **每日领免费积分**
- 图像：`jimeng image generate/edit/upscale`，jimeng 5.0/4.6/4.5 系列（即梦图片=Seedream 系），9 种比例、2k/4k → **替代 GPT Image 场景合成，走免费积分**
- 视频：`jimeng video generate`，模式 `text_to_video / image_to_video / first_last_frames / **omni_reference**`；模型 `jimeng-video-seedance-2.0 / 2.0-fast / 3.5-pro`，港日新区还有 veo3/sora2
- `--json` 全程结构化输出；`task wait/get/list` 任务管理

**源码级审查结论（关键）**：
1. **omni_reference 模式的 CLI 参数只暴露了 `--image-file`×9 和 `--video-file`×3，没有 `--audio-file`**——但底层就是 Seedance 2.0 Omni（与 apiz 的 super-seed2 同一模型，上游支持 3 段音频），即梦网页版多参考也支持音频输入。**给 jimeng-cli 补一个 audio 槽位是小改动**（`aigc_draft/generate` 的素材类型加 audio，上传复用 `get_upload_token` 链路）。
2. **即梦网页版有独立「数字人·对口型」功能**（照片/视频 + 音频 → 口型同步视频，支持大师模式和动物对口型，免费额度可用），同走 mweb API + sessionid。**jimeng-cli 尚未封装此功能**，用现有 token 池逆向封装一个 `jimeng lipsync` 命令是第二小的改动，却是**数字人口播最对口的免费通道**。

---

## 三、关键架构决策（v2 修订：原生配音升为主力）

> **v1 曾把「Seedance 原生配音」仅当兜底、主张 TTS 前置。经深度调研修正：
> Seedance 原生配音与原版 Grok 是同一范式，应为主力；TTS 前置降级为「指定音色」场景的选项。**

### 3.0 调研证据（为什么改判）

**Seedance 原生配音是一等能力，且音色一致性比 Grok 有结构性改善：**
1. **时间轴脚本块**：`[AUDIO: 0-4s] She says: "台词"` 写进提示词，台词即成真语音，原生音画联合生成（非两阶段拼接），音素级口型同步 8+ 语言、立体声（[Seedance 2.0 Sound Guide](https://www.seedance2pro.net/blog/seedance-2-sound-guide)、[声音设计与对白提示词](https://blog.csdn.net/gitblog_00562/article/details/167270573)）——与 Grok「引号台词」用法完全同构。
2. **脸→声关联**：Seedance 2 会从面部照片重建音色（"记得这个人听起来像什么样"，[Reddit 讨论](https://www.reddit.com/r/singularity/comments/1r0yr96/)）——固定同一张角色参考图，跨段音色天然趋同；配合 persona 固定音色描述句，一致性远好于 Grok 时代的裸提示词。
3. **音频参考是原生的，不是后期贴轨**：官方明确音频输入「驱动节奏、配乐、**人声口型**」，音视频同一架构生成（[API_Doubao 技术解析](https://blog.csdn.net/API_Doubao/article/details/163540192)）——即「锚定段」技法成立：第 1 段原生生成的配音可作为后续段的 @音频 参考，把音色钉死（P0 实测确认）。
4. **Seedance 2.5：单次 30 秒 + 局部编辑**：最多 30 图/10 视频/10 音频参考，按时间段控制叙事、**只重生成想改的片段**（[CSDN 深度评测](https://blog.csdn.net/qq_36120267/article/details/164457477)）——大段少切 = 少漂移机会；念错一句可局部重拍，不用整段重来。
5. **长内容官方路径就是分段生成 + 后期拼接**（[API_Doubao](https://blog.csdn.net/API_Doubao/article/details/163540192)）——原版脚本结构不变。
6. **官方教学明确单说话人可靠性最高**；口型同步四规则：嘴可见、正脸、动作少、短句（[Sound Guide](https://www.seedance2pro.net/blog/seedance-2-sound-guide)）——口播天然全中。

**残留风险（沿用原版已验证的解法）**：无音频参考时每次生成音色仍可能不同——原版 `voicefx/unify.py`（频谱匹配+去齿音+同房间混响）与 whisper 回听 QC 就是为这类漂移建的，**原样沿用**；再加「锚定段」参考把漂移压到更低。

### 3.1 v2 主架构：原生配音为主，TTS 为「指定音色」选项

| | 主力：Seedance 原生配音 | 选项：TTS 参考（指定音色时） |
|---|---|---|
| 声音从哪来 | 模型生成：固定角色参考图（脸→声）+ persona 固定音色描述句 + 锚定段音频参考 | edge-tts / `apiz speak` / 克隆声作 @音频 音色参考 |
| 口型 | 原生联合生成，音素级 | 同样原生联合生成（音频参考驱动人声口型），非后期贴轨 |
| 段长 | 即梦 2.0：≤15s/段；apiz 2.5：≤30s/段 | 音频实际时长（0 估算误差） |
| 时间轴 | whisper 回听对齐（原版 align.py 沿用） | edge-tts WordBoundary 免费直出 |
| 音轨 | 各段原生音轨 → unify.py 统一 | 成片铺 TTS 原轨 |
| 改一句 | whisper 定位 → 局部重生成（2.5）或重拍该段 | 改 TTS 文本重新合成即可 |
| 成本 | 即梦免费积分 ≈0；apiz 2.5 备份 | TTS ≈0；生成同样走上述通道 |
| 额外开发 | **零**（jimeng-cli 现状可用） | jimeng 通道需补音频槽位/对口型命令（P1） |

### 3.2 生成通道（v2 按优先级重排）

| 通道 | 原理 | 成本 | 状态 |
|---|---|---|---|
| **A. Seedance 原生配音 · 即梦**（新主力） | 角色参考图 + `[AUDIO]`/引号台词 + 固定音色描述 + 锚定段音频参考 → 原生音画出片 | 即梦免费积分 ≈0 | **jimeng-cli 现状即可用，零改造** |
| **B. Seedance 原生配音 · apiz 2.5**（精修/长段） | 同上，30s 单段 + 局部编辑 + 跨语言声线统一 | ≈50 积分/秒（单段重拍/精修用） | apiz CLI 现状可用 |
| **C. TTS 参考 · 音频驱动**（指定音色时） | edge-tts/克隆声作 @音频 音色+口型参考 | 即梦免费 或 apiz 付费 | apiz super-seed2 支持 3 段音频参考；**参数名需 P0 实测**；即梦通道需补 CLI 音频槽位 |
| **D. 即梦对口型**（照片+音频→说话，P1 加命令） | 专用对口型模型，大师模式加动作 | 即梦免费额度 | 需给 jimeng-cli 加 `lipsync` 命令（设施现成） |

**推荐组合**：默认 A；30 秒大段/精修/局部重拍用 B；用户要指定音色或克隆本人声时 C；D 作为 C 在即梦免费通道的落地形态。

### 3.3 各环节的工具映射总表

| 环节 | 原版 | 新版 | 花费变化 |
|---|---|---|---|
| 口播视频+配音 | Renoise Grok 17积分/秒 | **即梦对口型（A）** / apiz super-seed2（B） | 大幅下降→≈0 |
| TTS | Grok 原生 / MiMo（要 API key） | **edge-tts**（默认）/ `apiz speak` Minimax（升级）/ `voice-clone`（克隆本人声） | ≈0 |
| 场景合成图 | GPT Image 2.5，23积分/张 | **`jimeng image generate`（jimeng 5.0，免费分）**；apiz gpt-image 备份 | →≈0 |
| 回听 QC | whisper.cpp 必跑 | 降为**抽查**：`apiz align`（10积分/次）或本地 whisper 可选 | 依赖大幅简化 |
| 逐字时间轴 | whisper + difflib 对齐 | **edge-tts WordBoundary**（生成 TTS 时顺带产出） | →0 |
| 分片下载 | rangedl.py（Renoise CDN 易断） | 保留 rangedl 逻辑，apiz/即梦直链较稳 | 保留 |
| 字幕烧录 QC | 抽帧检查（Grok 坑） | 保留抽帧检查（Seedance 同款坑）+ `apiz` 字幕擦除兜底 | 保留 |
| 剪辑/包装 | Remotion 5 风格 + 48 组件 | **完全不动** | — |
| 景深字抠像 | macOS Vision | 保留 macOS-only，Phase 2 可选 rembg | 不变 |
| 换形象 | GPT Image 四视图 + Renoise material:id | `jimeng image edit` 四视图 + 参考图上传 apiz/即梦得 URL 存 persona | →≈0 |

---

## 四、新流程设计（v2：与原版同构，换通道不换范式）

```
你的内容
 → 0. 环境检查 doctor.sh（ffmpeg/python/node/jimeng 登录+积分/apiz 登录+余额；edge-tts 可选；whisper 可选）
 → 1. 诊断内容 → 推荐风格（不变，brief.json）
 → 2. 写稿 script.json（结构不变；默认 ≤15s/段走即梦 2.0，长段标 "long" 走 apiz 2.5 的 30s）
 → 3. build_plan.py：script → plan.json（每段 prompt：角色参考图 + [AUDIO] 台词脚本块 + persona 固定音色描述
       + shot 景别动作），报价（段数·秒数·通道·预估积分·余额）→ 用户确认
 → 4. generate_segments.py（替代 Renoise create_tasks/wait/download）：
       默认 jimeng video generate omni_reference（图参考）+ 台词提示词 → 原生配音口播
       精修/长段走 apiz seedance-2.5；锚定段产生后，后续段把首段音频作 @音频 参考（音色钉死，P0 验证）
       批量提交、限频、重试、轮询、下载到 gen/<id>.mp4、ffmpeg 解码校验
 → 5. assemble.py（沿用）：whisper 回听 QC（准确率比对）+ 抽帧查烧字幕 + 裁尾 + 统一规格 + 拼接 + loudnorm
       念错/音色漂移段 → apiz 2.5 局部编辑 或 重拍该段
 → 6. unify.py（沿用）：跨段频谱匹配 + 去齿音 + 同房间混响（有锚定段参考时漂移已很小，作保险）
 → 7. align.py（沿用）：whisper 逐字时间轴 → tl.json
       （纯旁白/画外音段若走 TTS，则该段用 WordBoundary 免费直出，不走 whisper）
 → 8. Remotion 剪辑渲染（原样保留：edit.json / pack / check_edit / 图鉴）

edge-tts 的三个固定出场场景（可选，不改变主流水线）：
  ① 用户要指定音色 / 克隆本人声 → 音频作 @音频 参考（通道 C/D）
  ② 纯旁白、画外音、不出镜段落 → 直接 TTS 铺轨，省一次生成
  ③ 外语段需要精确发音控制时 → TTS 参考兜底
```

---

## 五、文件级改造清单

```
skills/digital-human-koubo/
├─ SKILL.md                        【重写】流程改为 3.4 节；红线改「apiz/即梦积分先报价」；工具清单更新
├─ persona.json                    【改】renoise 块 → media 块（参考图本地路径 + apiz/即梦 URL）；
│                                   model 块 → channels 块（jimeng-lipsync / apiz-superseed2 / jimeng-native 三通道及价格）；
│                                   voice 块 → tts 块（engine: edge 默认，音色映射表 zh/en/ja/…，语速，风格描述）
├─ references/
│  ├─ voice.md                     【重写】edge-tts 音色菜单（中文/多语言）+ apiz speak/clone/design 用法
│  ├─ install.md                   【重写】去 Renoise MCP；apiz auth login、jimeng login/token receive、edge-tts
│  ├─ style-menu.md                【不动】
│  ├─ packaging*.md/json           【不动】
│  └─ new-avatar.md                【改】四视图改 jimeng image edit；参考图 → apiz upload URL 写回 persona
├─ scripts/
│  ├─ tts.py                       【新增·可选】指定音色场景（克隆/Minimax/多语言精确发音）才用：
│  │                                   生成 @音频 参考或纯旁白轨；SubMaker 词级时间戳供旁白段打轴
│  ├─ build_plan.py                【替代 build_tasks.py】plan.json + 报价（通道 A/B/C 比价、锚定段标记）
│  ├─ generate_segments.py         【新增】通道提交/轮询/下载/校验：jimeng omni（台词脚本块）+
│  │                                   apiz seedance-2.5（长段/精修/局部重拍）+ 可选音频参考通道
│  ├─ assemble.py                  【保留·微调】whisper 回听 QC、抽帧查字幕、裁剪、拼接逻辑全部沿用；
│  │                                   ids.json 的 taskId 换成新通道任务号，下载路径规则同步
│  ├─ align.py                     【保留】逐字时间轴逻辑不变；旁白段可选 WordBoundary 直出
│  ├─ unify.py / rangedl.py / cutout_video.py / make_assets.py / new_edit.sh / check_edit.py 【保留】
│  └─ doctor.sh                    【改】检查项：ffmpeg / python / node / jimeng(token+points) / apiz(auth+balance)；
│                                   edge-tts 标可选；whisper 从必需降为「剪 16:9 长片才需要」可选
├─ templates/（huazi-916、packaging、reference/） 【完全不动】
└─ assets/                         【保留】
```

**外部工作项（P1 前置）**：
1. fork jimeng-cli → `jimeng lipsync <image> <audio>` 命令（或独立 `scripts/jimeng_lipsync.py` 直调 mweb API，复用其 token 池文件）。改动点：`get_upload_token` 传音频、`aigc_draft/generate` 换对口型算法的素材结构、轮询复用 `task wait`。
2. jimeng-cli omni 模式加 `--audio-file`（可选，让通道 C 也能参考音频）。

---

## 六、成本对比（27 秒 5 段口播为例）

| 项目 | 原版（Renoise） | 新版主力（即梦+edge-tts） | 新版备份（apiz） |
|---|---|---|---|
| 口播生成 | 5 段 × ~30s × 17 = **≈482 积分** | **≈0**（即梦每日免费分；对口型单次消耗极低） | 30s × ~50 = ≈1500 积分（仅单段精修用） |
| 场景图 | 1 张 23 积分 | 0（jimeng 5.0） | 23 积分 |
| TTS | 含在视频里 | 0（edge-tts） | 少量（Minimax） |
| 时间轴 | whisper 本地（免费但重） | 0（WordBoundary） | 抽查 align ≈30 积分 |
| 依赖安装 | Renoise MCP + whisper.cpp+1.5GB 模型 | npm 一装 + pip 一装 | — |
| **合计** | **≈505 积分/条** | **≈0–10 积分/条** | 按需 |

---

## 七、分阶段实施计划

### P0 · 冒烟实测（先花小钱把不确定性清零，预估 <100 apiz 积分 + 即梦免费分）
1. `npm i -g jimeng-cli && jimeng login`（CN 区），`token receive` 领分、`token points` 确认；`image generate` 一张场景图验证免费链路。
2. **通道 A 实测（新主力，最优先）**：即梦 omni_reference + 角色参考图 + `[AUDIO: Xs]` 台词脚本块 + 固定音色描述，生成 2 段不同台词的口播：
   - 中文念字准确率、烧字幕情况（whisper 回听 + 抽帧）
   - **两段音色是否趋同**（同角色图 + 同音色描述）；再做「锚定段」验证：把第 1 段音频作 @音频 参考生成第 3 段，确认音色被钉住
   - 实测单段消耗积分，回填报价模型
3. **通道 B 实测**：apiz `--model apiz/seedance-2.5` 30 秒长段一条，验证长段口播质量与局部编辑入口。
4. **通道 C 参数实测**：`apiz upload` 一段 edge-tts 音频 → `apiz generate --model st-ai/super-seed2 --image-url <数字人图> --params '{"audio_url":"..."}'`（字段名以 400 报错提示为准）→ 确认音频参考是「音色复刻+新台词」还是「照播原文」，回填通道 C 的定位。
5. 用通道 A 零改造端到端跑通一条 3 段 27 秒样片，验证 Remotion 层无需改动。

### P1 · 核心管线（改造主体）
按第五节清单落地：build_plan.py → generate_segments.py（A/B 双通道 + 锚定段）→ assemble/unify/align 沿用微调 → persona.json/SKILL.md/voice.md/install.md/doctor.sh 重写 → jimeng lipsync / 音频槽位（通道 C/D）→ 全流程出完整样片回归（对比原版成片质量）。

### P2 · 增强（可选）
- `apiz voice-clone` 接入 voice.md 的「克隆本人声」流程（替代 MiMo）；
- 字幕擦除（`volcengine/vod/subtitle-erase`）接入烧字幕自动修复；
- cutout_video.py 加 rembg 跨平台抠像；
- finance-explainer 风格 A 引擎的同步迁移（本仓库快照未含该目录，需从上游补）；
- jimeng-cli omni `--audio-file` 上游 PR。

---

## 八、风险与待实测项

| 风险 | 影响 | 缓解 |
|---|---|---|
| apiz super-seed2 音频槽位字段名未知 | 通道 B 提交失败 | P0 实测；400 报错会提示参数；同时验证 `apiz/seedance-2.5`（描述明确含音频参考） |
| 即梦对口型 API 未公开文档 | 通道 A 需逆向 | payload 从网页抓取；最坏情况通道 B/C 兜底，功能不缺失 |
| 即梦免费积分额度与限频波动 | 批量生成排队 | token 池多账号轮换（jimeng-cli 原生支持）；apiz 通道兜底 |
| edge-tts 情感表现力弱、偶发断流 | 音色平淡 | `--rate/--pitch` 调表现；`apiz speak` Minimax 一键切换；重试机制 |
| Seedance 偶发烧字幕（同 Grok 坑） | 画面脏 | 保留抽帧 QC + 重拍该段；P2 接字幕擦除 |
| 口型与 TTS 轨细微漂移（若模型重合成语音） | 特写可感知 | 成片一律铺 TTS 原轨静音视频轨（原版既有规则）；P0 实测确认漂移量 |
| jimeng-cli 为 GPL-3.0 | 分发合规 | fork 独立仓库/本地工具使用，不并入 MIT 主仓分发 |

---

## 九、参考来源

- 本机实测：`apiz --help` 全家桶、`apiz models list/info`（super-seed2/seedance-2.5/minimax-h3 描述原文）、`apiz account balance`（791.99 积分）、edge-tts 7.3.1 合成 + SRT 实测、jimeng-cli 0.3.9 dist 源码审查（端点/参数/无 audio 槽位结论）
- [jimeng-cli (npm/GitHub Algovate)](https://github.com/Algovate/jimeng-cli) · [npm 页面](https://www.npmjs.com/package/jimeng-cli)
- [即梦 AI 官网（数字人·对口型入口）](https://jimeng.jianying.com)
- [Seedance 官方页（字节）](https://seed.bytedance.com/zh/seedance) · [火山引擎 Seedance API 文档](https://www.volcengine.com/docs/82379/1520757)
- [Seedance 2.0 Sound Guide（口型同步规则、@音频 对白参考语法）](https://www.seedance2pro.net/blog/seedance-2-sound-guide)
- [Reddit：audio as an input 是最被低估的功能（时间轴脚本块）](https://www.reddit.com/r/Seedance_v2/comments/1uf6hrz/the_most_underused_seedance_20_feature_audio_as/)
- [Seedance 2.0 声音设计与对白提示词详解（CSDN）](https://blog.csdn.net/gitblog_00562/article/details/167270573)
- [音视频联合多模态视频生成模型能力与实践（API_Doubao：音频驱动人声口型、长内容分段官方路径）](https://blog.csdn.net/API_Doubao/article/details/163540192)
- [Reddit：Seedance 2 从面部照片重建声音（脸→声关联证据）](https://www.reddit.com/r/singularity/comments/1r0yr96/)
- [Seedance 2.5 深度评测：单次 30 秒、多参考（30图/10视频/10音频）、局部编辑（CSDN）](https://blog.csdn.net/qq_36120267/article/details/164457477)
- [Seedance 2.0 实操：节奏、口型与转场（CSDN）](https://blog.csdn.net/weixin_32238157/article/details/162136328)
- [即梦 AI 多素材创作：声画对齐实操（博客园）](https://www.cnblogs.com/zi-rou-chuan/p/22422731)
- 价格基准：`~/.agents/skills/video-clone-lite/references/models.md`（2026-09-21 实测）
