# 制作手册：数字人、素材、合成

生成默认 **apiz MiniMax-H3**（480p 12 积分/秒 + context 7/次，人物真实感最好）；即梦 dreamina CLI 为备用通道（**积分很贵且不免费**）。台词核验走 apiz align（10 积分/次）；旁白占位 **edge-tts 免费**。生成前一律先报价 → 给用户看模型、提示词、数量、总价、余额 → 等明确同意。

## 1. 主播形象（定妆照）

- `dreamina image generate`（即梦图片，即梦积分）：`--prompt "书房中景…" --ratio 16:9 --resolution_type 2k`；或 `dreamina image edit --image 用户照片 --prompt "keep her face, hairstyle and outfit exactly the same, …"`。
- 构图：书房中景、人物居中、头在上三分之一、**两侧留白**（放卡片和图表）；专属道具：暖黄霓虹名字灯、玩偶、一盏标志性台灯。
- 布景要和被参考的频道明显不同（原频道 v1 是客厅霓虹、v2 是白书架；示例集用胡桃木书架 + 绿色台灯）。
- **身份核查**：用户给的脸如果被描述为某位真实创作者，或与前一张被描述为真人的照片五官、饰品一致只改了发型眼镜，不要用；纯文字生成或换一张确实不同的原创脸。

## 2. 数字人两方案

**默认主力：MiniMax-H3（apiz 通道）**——2026-10-31 实测对比后用户定版：人物真实感明显优于即梦 Seedance（皮肤纹理、微表情更「真人」），23 秒出片。
**即梦通道降级为备用**：即梦积分很贵且**不免费**（没有任何每日免费积分），仅在 H3 不可用时兜底。

| | A：MiniMax-H3 原生说话（默认） | B：即梦 multimodal2video 音频驱动（备用） |
|---|---|---|
| 输入 | 定妆照（必须真 16:9 横构图，见下）+ 提示词里写台词 | 定妆照 + 该拍音频（voice/audio/<id>.wav） |
| 口型 | 与它自己生成的声音天然一致（生成后跑 sync_beats.py 重打轴） | 跟着给定音频逐字同步 |
| 真实感 | **强**：皮肤纹理真实（2026-10-31 用户验收定版） | 偏「AI 蜡像感」 |
| 价格 | apiz：480p 12 积分/秒 + context 7/次；768P 18/秒；1080p 28/秒 | 即梦 mini ≈6 即梦积分/秒（贵，不免费） |
| 时长 | 4–15 秒/拍 | 4–15 秒/拍 |
| 声音 | H3 自己配（成片用它自带的音轨，sync_beats 打轴） | **你的最终音频**（自录/TTS/克隆声） |
| 脚本 | `python3 scripts/h3_beats.py episode.json anchor.png gen [--resolution 480p]` | `dreamina_beats.py --mode audio`（备用） |

**H3 硬规则（实测踩坑）**：
- **首帧图必须本身是真 16:9 横构图**。H3 的 adaptive ratio 严格照抄首帧构图：给模糊补边的 16:9 图，成片就带模糊边条，提示词改不动。竖版照片先用 `fal-ai/nano-banana-pro`（apiz，≈60 积分）扩图成真横版：人物不变居中、两侧自然延伸书房场景，再做 anchor。
- 参数走 content 数组：`content=[{type:text},{type:image_url,image_url:{url},role:first_frame}]`、`duration` 4–15 整数、`resolution` 480p/768P/1080p。
- **带货/多参考**：role 规则实测——不带 role 的图 = 首帧（最多 1 张）；`role:"reference_image"` 是参考图，**可与另两图连用但不能与 first_frame 混用**。带货套路：两张图都标 `reference_image`，提示词用「参考图1是主播的样子和她的场景…参考图2是她的商品…」自然语言指代（2026-10-31 实测：商品还原、人物一致、口播零错字，10s 127 积分）。
- 提示词要点：固定机位中景、嘴部清晰、真实摄影质感、与参考图一致、无字幕无水印。
- **生成后必跑 `sync_beats.py`**（原生音轨接管 + apiz align 重打轴，offset=0）。
- 裁切输出必须 CFR 30fps（VFR 会让 Remotion 报 No frame found）。

**推荐组合**：全屏/侧移出镜拍全走 A；预算紧或 H3 不可用时小窗、被图表盖住的拍才用 B，或 3 段通用说话循环轮换。

### 接入
- A：`dreamina_beats.py --mode audio --public <engine>/public` 出片段 → **`sync_beats.py` 收尾（必跑）**：出镜拍一律改用原生片段自带的音轨当旁白（即梦口型与它自己的音频严格对应），裁掉首尾后按 apiz align 重打字级时间轴、重建 timings（offset 恒为 0，不需要校准）。教训：另铺 TTS 音轨 + 猜 offset 必错位（片内语音起点 0.08–0.27s 不等，且 Seedance 会对参考音频重新配话速）。
- B：`dreamina_beats.py --mode native` 产 gen/clips.json → `grok_beats.py episode.json gen/clips.json voice --public <engine>/public`（whisper 逐拍对齐、只裁首尾静音、写 host.json；这段逻辑与生成通道无关，原样可用）。
- 换音色（B 收尾）：把逐拍音频交给 apiz「保留节奏的换声」——`apiz upload` 音频 + `voice-clone`/`speak` 生成同文本新音色，按 timings 逐拍切回 audio/<id>.wav，重跑 build_timeline；口型不受影响。
- 抽检口型：截停顿处与说话处的脸部特写对比（停顿应闭嘴）。

## 3. 声音

- **主播自录（首选）**：`align_recording.py 录音 episode.json voice/` — 按停顿切段 whisper 对齐、重录取最后一遍、压长停顿。本地免费，与生成通道无关。
- **占位（免费）**：`narrate_edge.py narration.json voice --gap 0.22 --lead 0.3` —— edge-tts（小晓/云希等），词级时间戳来自合成事件本身，**不需要 whisper**，输出 timings.json 与 MiMo 版同契约。英文缩写写进 lexicon 拆字母读（GPU→G P U），型号写中文读法。
- **占位（MiMo，可选）**：narrate_mimo.py 仍在，有 MIMO_API_KEY 或要克隆声时用。
- **克隆声**：apiz `voice-clone`（10 秒–5 分钟干净样本，只克隆本人或授权者）→ 克隆音色合成逐拍音频 → 走 A 方案，口型自动跟克隆声。
- **不做**：从真实创作者的视频里截取声音做克隆参考。

## 4. 空镜、梗、贴纸

- 空镜静图：`apiz generate --model fal-ai/nano-banana-pro`（≈60 积分，16:9 真实质感）；动态空镜 `dreamina text2video`（即梦积分，贵，按需）。长拍用 10 秒片 + 引擎里的 Ken Burns 慢推。下载用 `dreamina query_result --submit_id=<id> --download_dir=...`。
- 素材库：`fetch_stock.py <id> "<英文关键词>" <public>/assets --kind photo|video`（Unsplash/Pexels/Wikimedia，自动记 credits.json 片尾致谢）。不变。
- 梗：原创 3D 卡通短片（同空镜做法），不用影视、综艺片段。
- 卡通贴纸：`dreamina image generate --prompt "…plain solid pure green background"`（即梦积分，很便宜），然后抠绿：
  ```python
  green=(g>120)&(g-np.maximum(r,b)>40); alpha=MinFilter(3)+GaussianBlur(1); 绿溢色：g=min(g,max(r,b)); 裁 bbox
  ```

## 5. 合成与出片（不变）

1. `build_timeline.py episode.json voice/timings.json <public> --assets assets.json --host host.json --bgm music/bgm.mp3 --badge "AI 生成数字人演示 · 非商用"`
   - 片段演示用 `--from c01 --to c11`；卡片 `until: "<cue>"`。
2. 抽帧：`npx remotion still Episode out/x.jpg --frame=N`（并行 6–8 张拼一张图看）；一定要看主播缩放的过渡中间帧。
3. 渲染：`npx remotion render Episode out/raw.mp4 --concurrency=6`（1080p 约 0.25× 实时）。
4. 出片：`ffmpeg -i raw.mp4 -c:v libx264 -crf 21 -pix_fmt yuv420p -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -b:a 192k -movflags +faststart 成片.mp4`。

## 6. 踩过的坑（即梦版）

- **multimodal2video 不跟随参考图比例**：默认 16:9， Finance 全是 16:9 所以 dreamina_beats 已显式传 `--ratio 16:9`；做竖屏衍生内容时注意。
- mini 单拍上限 15 秒：超长拍拆两拍，或接受 seedance2.5（VIP，先拍一条校准单价）。
- 提交即扣积分，队列慢时 `dreamina query_result` 慢慢拉；不要重复提交同一拍（`dreamina_beats.py` 的 tasks.json/clips.json 断点会防，手动重拍加 `--resubmit`）。
- 首次用某模型报 `AigcComplianceConfirmationRequired` = 要去即梦网页端用一次该模型完成首次确认。
- 字幕断句要按**原文标点**（对齐结果里没有标点）：build_timeline 用 timings 的 text + chars。
- Wan 片段 480p 拉到 1080p 会软的时代已过去：mini 直出 720p，全屏镜头够用；还嫌软就 2.5 直出 1080p。
- PiP 圆形头像：face 坐标填人脸在定妆照里的相对位置（示例 [0.5, 0.33]）。
- PIL / numpy 只在部分 Python 里有；ffmpeg 没有 drawtext，标注一律用 PIL。
- 不要扫描系统找 API key；检索 key 只读 ~/.config/xiaolin-explainer/keys.env。
