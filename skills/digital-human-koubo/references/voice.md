# 声音方案

默认 **Seedance 原生配音**（persona.json → voice.desc，每段一字不改，整片音色才统一）：
台词写进提示词（`她用普通话清晰地说："…"`），模型音视频联合生成、音素级口型同步。
跨段一致性三件套：固定同一张角色参考图（Seedance 会从脸推声音）+ 固定音色描述句 + 生成后跑 `voicefx/unify.py` 统一频谱（原版方案，实测齿音段间差 13.2→5.9 dB）。

## 什么时候不用原生配音

| 场景 | 做法 |
|---|---|
| 纯旁白 / 画外音 / 不出镜段 | `tts.py` 用 edge-tts 合成（免费），剪辑时单独铺轨 |
| 用户要指定音色（如小米腔、新闻腔） | `tts.py` 选 persona → voice.tts.map 里的音色 → 该段标 `"channel": "audio_ref"`，multimodal2video 拿音频作音色+口型参考 |
| 用户要自己的声音 | **海螺声音克隆**：`python3 scripts/voice_clone.py 样本.mp3 --name 我的音色`（apiz minimax/voice-clone；样本 mp3/m4a/wav、10 秒–5 分钟、≤20MB），脚本自动上传→克隆→试听 clone_test.mp3，voice id 填进 persona.json → voice.tts.cloned_voice_id；再走 audio_ref 通道 |

## edge-tts 音色速查（`python -m edge_tts --list-voices` 看全部）

| key | 音色 | 适合 |
|---|---|---|
| zh | zh-CN-XiaoxiaoNeural | 温暖亲切女声（默认） |
| zh-male | zh-CN-YunxiNeural | 阳光男声 |
| en | en-US-EmmaMultilingualNeural | 英语/多语 |
| ja / ko | ja-JP-NanamiNeural / ko-KR-SunHiNeural | 日/韩 |

音频要求：multimodal2video 的参考音频单段 ≤15 秒（seedance2.5 下 ≤30 秒），超了先拆段。

## 音质修整

- 原生配音多段有漂移 → `python3 scripts/voicefx/unify.py <输出目录> <片段…>`（复用旧段加 `--ref 旧目录`；场景/动物段加 `--scene`）
- TTS 旁白与原生配音混排时，各自 unify 后再统一响度
- 台词核验和字级时间轴：assemble.py 默认 `--qc align`（apiz align，10 积分/段，实测零错字）；零积分用 `--qc whisper`


## 海螺声音克隆（apiz，默认克隆通道）

- 触发：用户说「克隆我的声音 / 用我的声音配」时走这一步（用户需要时才加，平时跳过）。
- 命令：`python3 scripts/voice_clone.py <样本音频> --name <自定义voice_id>`
- 样本：mp3/m4a/wav，10 秒–5 分钟，≤20MB；安静房间、离麦 20 厘米、无混响。只克隆本人或明确授权者的声音。
- 流程：上传 → 克隆 → `apiz voices list` 的 user_voices 里确认 → 自动合成试听 clone_test.mp3 → 用户人耳确认。
- 克隆音色用法：`apiz speak --voice <voice_id>`（纯旁白）或填 persona.json → voice.tts.cloned_voice_id → tts.py 合成 → multimodal2video 音频驱动（口型跟克隆声）。
- 时效：克隆音色有过期风险（voices list 的 status 字段 active/expired），过期重跑脚本再克隆一次即可。
