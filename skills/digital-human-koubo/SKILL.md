---
name: digital-human-koubo
description: 用固定的数字人形象（白背心数字人 / 用户本人数字人 / 猫狗角色）做口播视频，先按内容推荐剪辑风格让用户选（小林式解说 / 网红花字口播 / 发布解读 / 保姆级教程 / 多主播多语言），自动套上从 MrBeast、MKBHD、影视飓风、Johnny Harris、Vox、半佛、差评等头部博主拆出来的 48 个包装组件（开场钩子、数字钉子、文字在人身后的景深字、证据截图、地图路线、弹幕、投票、复盘板…），再写稿 → 报价确认 → 即梦 dreamina CLI 分段生成（Seedance 原生配音+口型，mini 通道日常 ≈6 积分/秒）→ apiz align 逐段台词核验 → 声音统一 → Remotion 剪辑出片。指定音色/克隆声走 edge-tts + multimodal2video 音频参考。触发：用我的数字人讲这段、数字人口播、让白背心数字人说、用数字人 Skill、数字人带货 / 解读 / 教程 / 种草视频、做成小林说那样、加花字、加包装 / 加地图 / 加弹幕 / 开场加预告 / 文字放在人身后、做成 MrBeast 那种节奏、有哪些包装手法。不用于：换一个全新形象（先按 references/new-avatar.md 做形象）、冒充真人。
---

# 数字人口播（即梦版）

形象、声音、通道、报价规则固定在 `persona.json`；剪辑风格在 `references/style-menu.md`。每次照这里做，出来的就是同一个人、同一种风格。
生成主力是 **即梦官方 dreamina CLI**（`seedance2.0mini`，实测 6 即梦积分/秒、基本 0 排队）；台词核验和字级打轴用 **apiz CLI**；旁白/指定音色才用 **edge-tts**。

## 红线
- 生成花的是用户的即梦积分 / apiz 积分：**create 之前先报「段数 · 秒数 · 预估积分 · 余额」，等用户明确同意**。先拍第 1 段给用户确认形象和音色，再批量。重拍也要先报价。
- `generate_segments.py` 不加 `--yes` 是干跑（不花钱）；`assemble.py --qc align` 不加 `--yes` 只报 QC 花费。工具替你守着红线，但报价的话必须说。
- 不要用 `seedance2.0fast`：晚高峰免费队列会排几小时；日常一律 `seedance2.0mini`（persona 默认），30 秒长段/精修用 `seedance2.5`（VIP）。
- seedance2.5 单价未实测：第一次用先拍 4 秒校准，再报整单价。
- 成片标「内容由 AI 数字人演绎」（即梦自动加「AI 生成」角标，剪辑时可再补一致的声明）；场景、动物片段角上标「AI 生成」。
- 用户本人的形象（persona.json → other_hosts.me）只用在用户自己的片子里。
- 「小林式」只学结构和剪辑手法：不用真实创作者的脸、声音、布景和原句。
- 点名评价第三方产品的说法，要有出处或标「网友分析 / 个人体验」。展示素材只用用户自己的作品；带歌词字幕的片子不用。
- 只克隆/使用用户本人或明确授权的声音和脸。

## 流程

### 准备：先检查，有就跳过，缺才引导安装（每次新对话第一次用时做）
**原则：已经装好的一句话带过，不让用户重装；缺什么才给装法，装法给多种，先放用户当前用的那种。** 详细装法在 references/install.md。
1. **即梦 dreamina CLI**：终端跑 `dreamina user_credit`。
   - 返回积分 → 「即梦已登录，余额 X 积分」，接着干活。
   - 报找不到命令 → 引导安装（`curl -s https://jimeng.jianying.com/cli | bash`，官方安装器）。
   - 报未登录 → `dreamina login` 浏览器授权（OAuth 设备码，不用复制任何 key），不用重装。
2. **apiz CLI**：`apiz account balance` 有余额即可（QC 用）。没有 → `apiz auth login`。
3. **本机环境**（要剪辑时才需要）：`bash scripts/doctor.sh`。有的打 ✓ 不提；缺的它按系统列装法。
4. **数字人形象**：persona.json → media.reference_image 指向的本地文件存在就直接用；要用用户自己的照片 → 把照片放进 assets/ 改路径，全新四视图按 references/new-avatar.md。

### 0. 看内容 → 推荐风格 → 让用户选
按 `references/style-menu.md`：
1. 一行诊断（内容类型、有没有可展示的素材、适合的平台和时长）。
2. 推荐 2 个风格并说理由，把 `assets/styles/` 里对应的预览图发给用户。
3. 一次问完：风格 · 比例和时长 · 花字强度（克制 / 标准 / 热闹）· 主播（白背心 / 用户本人 / 两人接力 / 动物）。每题第一个选项是推荐项。Claude Code 用 AskUserQuestion，其他工具列编号。
4. 用户回「你定」就按推荐，并说一句按了什么。结果写进 `brief.json`，后面每一步按它来。

| 风格 | 比例 | 时长 | 剪辑实现 |
|---|---|---|---|
| A 小林式解说 | 16:9 | 3–20 分钟 | finance-explainer skill 的引擎（episode.json 拍表） |
| B 网红花字口播 | 9:16 | 30–120 秒 | `templates/huazi-916`（edit.json 驱动，三档花字） |
| C 发布解读 | 16:9 | 30–90 秒 | 参考实现 `templates/reference/launch-169` |
| D 保姆级教程 | 16:9 | 3–8 分钟 | 参考实现 `templates/reference/tutorial-169` |
| E 多主播多语言 | 16:9 | 3–7 分钟 | 参考实现 `templates/reference/multihost-169` |

### 1. 写稿 → script.json
按选定风格的稿子写法（style-menu.md 里每种都有）。每段一句或两句，10 秒左右（中文约 40–55 字，Seedance 实测约 5.4 字/秒），标 `shot`：`full`（全屏出镜）/ `pip`（画中画讲解）/ `vlog`（随意自拍口吻）/ `depth`（要做「文字在人身后」的段：中景、头顶两侧留背景）。外语段直接写目标语言台词并标 `"lang"`。
可选段级字段：`"channel": "long"`（超 15 秒的长段，走 seedance2.5）、`"channel": "audio_ref"` + `"tts": true`（指定音色/克隆声/纯旁白，先跑 tts.py）。

### 2. 计划 + 报价
`python3 scripts/build_plan.py script.json plan.json --purpose "<这段内容的目的，如 带货主播介绍福利>"`
→ 打印「N 段 · 秒数 · 预估即梦积分 · 余额」并写 plan.json。**把报价报给用户，等明确同意**；用户同意第 1 段先行的，加 `--only` 精神：generate 阶段先只跑第 1 段。

### 3. 生成
`python3 scripts/generate_segments.py plan.json`（干跑复核）→ 用户确认后 `--yes`。
- 提交 → 自动轮询 → 下载到 `gen/<id>.mp4` → ffprobe 校验 → `gen/manifest.json`。
- mini 一般 5–10 分钟/段；出现 `AigcComplianceConfirmationRequired` = 该模型要去即梦网页端先用一次。
- 单段失败/要重拍：`--only <id>` 只重跑那段（报价再来一遍）。
- 换场景（直播间/门店/街景）：先用 `dreamina image generate` 合成开场画面存 assets/，把它当该段参考图。

### 4. 质检 + 拼接
`python3 scripts/assemble.py script.json gen/manifest.json`（默认 `--qc align`：apiz align 逐段核验台词 + 拿字级时间，10 积分/段，工具会先报总价等 `--yes`）
- 准确率 < 85% 的段打 ⚠：先抽帧看（`ffmpeg -ss 秒 -i gen/<id>.mp4 -frames:v 1 f.jpg`）再决定重拍；真念错就重拍该段或用 seedance2.5 局部重拍。
- 每段抽 2–3 帧检查烧字幕（Seedance 偶尔也会烧，提示词写了无字幕也挡不住），有就重拍那段。
- 想零积分核验：`--qc whisper`（要装 whisper-cli）；快速预览：`--qc none`。

### 5. 声音统一 + 对齐
- 多段音色漂移就统一：`python3 scripts/voicefx/unify.py <输出目录> cut/*.mp4`（复用旧段加 `--ref`；场景/动物段加 `--scene`）。有锚定习惯的（同角色图+同音色描述）漂移很小，unify 作保险。
- 逐字时间轴：`python3 scripts/align.py script.json --out <工程>/src/tl.json`（吃 assemble 产出的 cut/words/，align 和 whisper 两种来源都认）。

### 6. 剪辑
按 brief.json 的风格剪：
- **B 花字口播**：`bash scripts/new_edit.sh huazi-916 <工程>` → 写 `src/edit.json`（关键词、表情、卡片、作品展示、号召，字段见 references/huazi.md）→ `python3 scripts/check_edit.py <工程>/src` → 抽帧 → 渲染。
- **A 小林式**：按 finance-explainer skill 的拍表和画面语法做；数字人口播片段放进 host.json。
- **C / D / E**：`bash scripts/new_edit.sh reference/<目录> <工程>`，换 tl.json，按段重写 Scene（templates/reference/README.md）。
- **包装（每种风格都做）**：按 `references/packaging-presets.json` 里这个风格的默认包装排——开场 30 秒按 open 顺序、正文保证 stimulus_every_s 秒内有一个新视觉事件、讲到 per_beat 里那类内容就用对应组件、recurring 全片挂着。组件写进 `pack` 数组（字段见 references/packaging.md），手法依据见 references/packaging-playbook.md。用户点名要的手法（「加地图」「开场加预告」「加弹幕」「换成 MrBeast 那种」）在默认基础上加减。用户问「有哪些包装」先发 `assets/packaging/图鉴.jpg`。景深字（文字在人身后）要先跑 `scripts/cutout_video.py` 抠像，见 references/packaging.md。
- 声音：数字人视频轨一定 `muted`，人声单独铺一条（unify 产出的 wav）；BGM 压在人声下约 20 dB。
- 抽帧检查一定看过渡的中间帧和零间隔衔接处（上一条的尾巴会盖住下一条）。

## 参考
- references/install.md：dreamina / apiz / 本机环境的装法（只在缺的时候用）
- references/style-menu.md：五种风格、内容诊断、怎么问用户、brief.json
- references/packaging.md：47 个包装组件的用法和参数（pack 写法、9:16 自动适配）
- references/packaging-playbook.md：头部博主实测结论（节奏、开场公式、字幕、声音、号召、红线），完整报告在 references/research/
- references/packaging-presets.json：五种风格各自的默认包装
- references/huazi.md：花字模板 edit.json 字段、九种卡片、三档强度、写法习惯
- persona.json：形象、参考图路径、三通道（mini 主力 / 2.5 长段 / audio_ref 指定音色）、提示词模板、动作库、QC 规则
- references/voice.md：声音方案（原生配音三件套 / edge-tts / apiz 克隆声）
- references/new-avatar.md：从一张照片做新形象
- references/edit-styles.md：各剪辑工程的入口文件和声音统一做法
- assets/styles/：五种风格的预览图（给用户选的时候发）
- assets/packaging/：包装组件图鉴（47 格总览 + 每个组件一张）
