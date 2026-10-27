# 制作手册：数字人、素材、合成

生成走 **即梦官方 dreamina CLI**（mini 实测 6 即梦积分/秒、基本 0 排队）；台词核验/备用 TTS/克隆声走 **apiz CLI**；旁白占位 **edge-tts 免费**。生成前一律先干跑报价（脚本不带 `--yes` 不花钱）→ 给用户看模型、提示词、数量、总价、余额 → 等明确同意。

## 1. 主播形象（定妆照）

- `dreamina image generate`（即梦图片，即梦积分）：`--prompt "书房中景…" --ratio 16:9 --resolution_type 2k`；或 `dreamina image edit --image 用户照片 --prompt "keep her face, hairstyle and outfit exactly the same, …"`。
- 构图：书房中景、人物居中、头在上三分之一、**两侧留白**（放卡片和图表）；专属道具：暖黄霓虹名字灯、玩偶、一盏标志性台灯。
- 布景要和被参考的频道明显不同（原频道 v1 是客厅霓虹、v2 是白书架；示例集用胡桃木书架 + 绿色台灯）。
- **身份核查**：用户给的脸如果被描述为某位真实创作者，或与前一张被描述为真人的照片五官、饰品一致只改了发型眼镜，不要用；纯文字生成或换一张确实不同的原创脸。

## 2. 数字人两方案（即梦版）

| | A：multimodal2video 音频驱动（首选） | B：image2video 原生说话 |
|---|---|---|
| 输入 | 定妆照 + 该拍音频（voice/audio/<id>.wav） | 定妆照 + 提示词里写台词 |
| 口型 | 跟着给定音频逐字同步（Seedance 原生联合生成，音素级） | 与模型自己的声音天然一致 |
| 表情 | 亲切自然、不夸张（口型优先） | 更灵动：眨眼、挑眉、手势丰富 |
| 价格 | mini 720p ≈6 即梦积分/秒（实测） | 同左 |
| 时长 | 4–15 秒/拍；>14 秒自动升 seedance2.5（VIP，4–30 秒，单价未实测先拍一条校准） | ≤15 秒/拍 |
| 声音 | **就是你的最终音频**（自录/TTS/克隆声），零换声 | 模型的声音，事后换音色（apiz，见 §3） |
| 脚本 | `python3 scripts/dreamina_beats.py episode.json voice --mode audio --yes` | `--mode native`，出片后 `grok_beats.py` 对齐写 host.json |

两个模式的提示词都内置在 `dreamina_beats.py`（要点：嘴部清晰、停顿闭嘴、固定机位、与参考图一致、无字幕无水印；「俏皮挑眉」之类会盖过口型，别加）。

**推荐组合**：有最终音频（自录/克隆声）的拍全部走 A；要表现力的全屏特写镜头可用 B + 事后换音色；圆形小窗和被空镜盖住的拍用 B 480p（只取声音氛围）或 3 段 10 秒通用说话循环轮换，省约 40% 口型费用。

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

- 空镜：`dreamina text2video --prompt "…slow dolly, no readable text or logos…" --duration 5 --video_resolution 720p --model_version seedance2.0mini`（≈30 积分/5 秒）。长拍用 10 秒片 + 引擎里的 Ken Burns 慢推。下载用 `dreamina query_result --submit_id=<id> --download_dir=...`。
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
