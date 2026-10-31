<div align="center">

# Digital Human Koubo · AI 数字人口播

**One photo + one sentence → a finished talking-head video with a digital human.**
Script, lip-synced AI presenter, voice clean-up, captions, and pro-YouTuber-style packaging — fully automated by your AI agent.

**English** · [简体中文](README.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)
![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-orange)
[![即梦 dreamina CLI](https://img.shields.io/badge/video-%E5%8D%B3%E6%A2%A6%20dreamina%20CLI-ff355f)](https://jimeng.jianying.com)
![Remotion](https://img.shields.io/badge/edit-Remotion%204-0b84f3)

<img src="docs/images/cover.jpg" width="820" alt="One photo + one sentence → a 27-second livestream sales ad">

</div>

> This 27-second livestream ad has no real presenter. Face, voice, studio, captions and the price animation are all AI.
> The only input was one sentence: *"Use this digital human to make a 30-second livestream ad for the WorkBuddy course — 10 lessons, ¥99, was ¥999."*
> Generation defaults to **MiniMax-H3 via apiz** (best measured realism): the talking-head part of a 27-second ad costs about **100 apiz credits**; our measured 90-second finance explainer spent ≈780 credits on 6 H3 presenter beats. Dreamina (Jimeng) remains as a fallback channel — its credits are pricey and **not free**.

---

## Demos

Click a GIF (or "Watch") to play the full video. Every demo below was produced with this repo.

| | | |
|:---:|:---:|:---:|
| <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/workbuddy-live-ad.mp4"><img src="docs/gifs/workbuddy-live-ad.gif" width="230"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/renoise-koubo-huazi.mp4"><img src="docs/gifs/renoise-koubo-huazi.gif" width="230"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/text-behind.mp4"><img src="docs/gifs/text-behind.gif" width="300"></a> |
| **Livestream sales ad** · 9:16 · 27 s<br>Style B + depth-text price ¥999→¥99<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/workbuddy-live-ad.mp4) | **Product recommendation** · 9:16 · 89 s<br>Animated captions, emoji, picture-in-picture<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/renoise-koubo-huazi.mp4) | **Text behind the presenter** · 5 s<br>Vision person matting, 3-layer composite<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/text-behind.mp4) |

| | |
|:---:|:---:|
| <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-ep2.mp4"><img src="docs/gifs/tutorial-ep2.gif" width="400"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-digital-human-upgrade.mp4"><img src="docs/gifs/tutorial-digital-human-upgrade.gif" width="400"></a> |
| **Step-by-step tutorial** · 16:9 · 4:36<br>The digital human teaches how she was made (Style D)<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-ep2.mp4) | **Digital human, upgraded** · 16:9 · 5:55<br>Two presenters, 6 languages, 4 scenes, cat & dog (Style E)<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/tutorial-digital-human-upgrade.mp4) |
| <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/memt-launch.mp4"><img src="docs/gifs/memt-launch.gif" width="400"></a> | <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/xiaolin-style-explainer.mp4"><img src="docs/gifs/xiaolin-style-explainer.gif" width="400"></a> |
| **Launch breakdown** · 16:9 · 39 s<br>Presenter on the side, code B-roll on the right (Style C)<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/memt-launch.mp4) | **Finance / tech explainer** · 16:9 · 2:21<br>Charts, documents, chapter cards (Style A)<br>[▶ Watch](https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/xiaolin-style-explainer.mp4) |

<div align="center">
<a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/packaging-gallery.mp4"><img src="docs/gifs/packaging-gallery.gif" width="560"></a><br>
<b>Packaging component gallery</b> · 48 components · 2:40 · <a href="https://github.com/andyhuo520/digital-human-koubo/releases/download/v1.0.0/packaging-gallery.mp4">▶ Watch</a>
</div>

> All presenters in the demos are AI digital humans and every video is labelled "内容由 AI 数字人演绎" (performed by an AI digital human). The male presenter is the author's own digital twin, made from his own photo.

---

## What it does

- **Digital human from one photo** — a fixed presenter (face, outfit, voice description, prompt template) stored in `persona.json`, so every video is the same person. Composite her into any scene (livestream studio, shop, classroom, study) with a Dreamina-generated portrait first, then make her talk.
- **Lip-synced talking clips** — the script is split into segments and generated by default through **MiniMax-H3 (apiz)**: put the line in the prompt and the model dubs it natively with the best measured realism. Fallback: the official 即梦 (Dreamina) CLI — `multimodal2video` audio-driven lip-sync (your own recording / TTS audio as the reference) and `image2video` native speech.
- **Cost gate** — every generation script dry-runs by default: the agent quotes *segments · seconds · credits · balance* first and waits for your `--yes`. It generates segment 1 for you to check before batching the rest.
- **Quality control** — every segment is verified with `apiz align` (word-level alignment against the script — zero misreads in our tests; it also produces the word-level timing for captions), plus frame inspection (Seedance sometimes burns subtitles into the picture; those segments get re-shot). Local whisper still works as a free option.
- **Voice unification** — a fixed reference photo (Seedance infers the voice from the face) + a fixed voice description + 1/3-octave spectral matching and de-essing (`voicefx/unify.py`, sibilance spread 13.2 dB → 5.9 dB in our tests), so 30 separately-generated clips sound like one recording.
- **5 editing styles, chosen for your content** — the agent diagnoses your content, recommends 2 styles with preview images and asks you everything in one go (style · ratio & length · caption intensity · presenter).
- **48 packaging components** — measured frame-by-frame from 25 videos by top creators (MrBeast, Mark Rober, Ryan Trahan, MKBHD, MediaStorm/影视飓风, 何同学, Johnny Harris, Vox, Kurzgesagt, 回形针, 半佛仙人, 差评, 毕导). Each style has a default packaging recipe; add or remove techniques by just asking.
- **Text behind the presenter** — big words / numbers between the background and the person (macOS Vision person segmentation → transparent video → 3-layer composite).
- **Multi-language** — English, Japanese, Korean, French, Spanish, Arabic tested; narration and custom voices use edge-tts (free), cloned voices via apiz.
- **Works with your agent** — a standard `SKILL.md` Agent Skill plus scripts. **No MCP server required** — any agent that can load skills and run local commands (Dreamina CLI / ffmpeg / Python / Node) can drive it.

## How it works

```
your content ──► 0. setup check (Dreamina CLI / apiz / ffmpeg — skip what you already have)
                 1. diagnose content → recommend 2 of 5 styles → ask once → brief.json
                 2. script.json (≤15 s per segment, ~5.4 Chinese chars/s)
                 3. quote credits → wait for "yes" → generate segment 1 → you check → batch
                 4. generate (Dreamina) → download & verify → apiz align back-check → frame check
                 5. voice unification (spectral match + de-ess + shared room)
                 6. word-level timeline (tl.json)
                 7. edit in Remotion: style template + default packaging (+ your requests)
                 8. render → check mid-transition frames → loudness (-14 / -16 LUFS)
```

<p align="center"><img src="docs/images/ad-breakdown.jpg" width="820" alt="The 5 segments of the livestream ad and the packaging used in each"></p>

---

## Supported agents

The skill is a folder with a `SKILL.md` (the open Agent Skills format) plus Python / shell / Remotion scripts. To run the **whole** pipeline an agent now needs only two things:

1. **Load Agent Skills** (a skills folder or skill upload),
2. **Run commands on your computer** (即梦 Dreamina CLI, apiz CLI, ffmpeg, Python, Node — for generation, QA and editing).

Generation runs on your own apiz / Jimeng accounts. **No remote MCP server involved.**

| Agent | Skills | Local commands | Status |
|---|---|---|---|
| **Claude Code** | `~/.claude/skills/` | ✅ | ✅ Tested — this repo was built with it |
| **Codex** (CLI / desktop) | `~/.codex/skills/` | ✅ | ✅ Expected to work (same scripts) |
| **OpenClaw** | skills folder per OpenClaw docs | ✅ | ⚙️ Should work |
| **WorkBuddy** | Skills → import the folder / zip | ✅ desktop agent | ⚙️ Should work — menu names may differ by version |
| **豆包 (Doubao)** · **千问办公 (Qwen Office)** · **纳米Work (NamiWork)** and other agent products | import if the product supports Agent Skills | needed for generation & editing | ⚙️ Works if the product supports the 2 requirements above; check its docs |
| **Claude desktop / claude.ai** | upload the skill zip in Settings | ⚠️ sandbox only | Script writing, scene design & quoting work; generation and local editing need a shell agent |

> If your agent can only chat (no local commands), use it to **write the script and the beat sheet**; then run generation and editing with Claude Code / Codex, or by hand with the commands in [`SKILL.md`](skills/digital-human-koubo/SKILL.md).

---

## Installation

### 1 · Get the code

```bash
git clone https://github.com/andyhuo520/digital-human-koubo.git
cd digital-human-koubo
```

### 2 · Install the two skills into your agent

The repo contains two skills: `digital-human-koubo` (main) and `finance-explainer` (the engine for Style A, the finance / tech explainer).

**Claude Code**
```bash
mkdir -p ~/.claude/skills && cp -R skills/digital-human-koubo skills/finance-explainer ~/.claude/skills/
```
**Codex**
```bash
mkdir -p ~/.codex/skills && cp -R skills/digital-human-koubo skills/finance-explainer ~/.codex/skills/
```
**WorkBuddy / OpenClaw / other agents** — zip the two folders and import them in the product's *Skills* page, or copy them into its skills directory (see the product's docs):
```bash
cd skills && zip -r ../digital-human-skills.zip digital-human-koubo finance-explainer && cd ..
```

### 3 · Install the apiz CLI (primary generation) and the Dreamina CLI (fallback)

Generation defaults to **MiniMax-H3 via apiz**; Dreamina is a fallback (**credits are pricey, not free**).

```bash
curl -s https://jimeng.jianying.com/cli | bash   # installs the dreamina CLI (same command in Git Bash on Windows)
dreamina login                                   # open the URL, enter the code, done
dreamina user_credit                             # check your balance — if this works, you're set
```

> Daily driver: `seedance2.0mini` (measured ≈6 Jimeng credits/s at 720p, virtually no queue). **Avoid `seedance2.0fast`** — its free queue can stretch for hours at peak time. `seedance2.5` does 30-second takes and is VIP-only.

### 4 · Install the apiz CLI — script verification / TTS / voice cloning

```bash
curl -fsSL https://data.apiz.ai/cli/install.sh | bash   # or see apiz.ai
apiz auth login                                          # store your API key
```

### 5 · Local tools (for generation, QA and editing)

| Tool | macOS | Windows | Linux |
|---|---|---|---|
| ffmpeg | `brew install ffmpeg` | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` |
| Python 3 + numpy + Pillow | `brew install python` then `python3 -m pip install numpy pillow` | `winget install Python.Python.3.12` | `sudo apt install python3-pip` |
| Node.js 18+ (Remotion) | `brew install node` | `winget install OpenJS.NodeJS.LTS` | `nvm install --lts` |
| edge-tts (optional, narration / custom voices) | `python3 -m pip install edge-tts` | same | same |
| whisper.cpp (optional, zero-credit back-check) | `brew install whisper-cpp` | [Releases](https://github.com/ggerganov/whisper.cpp/releases) | build from [source](https://github.com/ggerganov/whisper.cpp) |

One-command check — it skips what you have and lists install options for what's missing:
```bash
bash ~/.claude/skills/digital-human-koubo/scripts/doctor.sh
```

The **text-behind-presenter** effect uses Apple Vision and needs **macOS**; everything else is cross-platform (including Windows — this repo is actively run on Windows).

### 6 · Sound effects & placeholder music

The repo ships **no third-party audio**. Generate an original set of 30 sound effects and a placeholder background track (pure code, no copyright):
```bash
python3 ~/.claude/skills/digital-human-koubo/scripts/make_assets.py
```
`new_edit.sh` / `setup_engine.sh` also run this automatically for every new project. For a better soundtrack, drop any track you have the rights to at `<project>/public/music/bgm.mp3`.

---

## Quick start

Talk to your agent in plain language:

```text
用我的数字人 Skill 讲这段：……（paste your content）
Use my digital human skill to make a 30-second livestream ad: WorkBuddy course, 10 lessons, ¥99 (was ¥999).
Make a 90-second finance explainer: a 15× stock crashes 36% in one day.
Add a map route when she mentions these countries. / Put "¥99" behind her. / Add a teaser cold open.
把包装组件图鉴发我看看  (show me the packaging gallery)
```

What happens next:
1. Setup check — anything already installed is skipped.
2. A one-line diagnosis + 2 recommended styles with preview images, and one round of questions.
3. Script + scene design + **credit quote** → you approve → segment 1 → you approve → the rest.
4. QA, voice clean-up, editing with the style's default packaging → the finished MP4.

---

## Make your own digital human

1. Pick a photo: frontal face, even light, hair off the face, mouth closed. **Only your own photo or one you have permission to use.**
2. Have the agent generate a portrait or a 4-view sheet (`dreamina image` / `image edit`, 16:9 2k, a few Jimeng credits) so the face stays the same from every angle; drop it into `assets/`.
3. Shoot one test take with the same line (`dreamina_beats.py` / `generate_segments.py`, a few credits) and judge the face, the lip-sync and the voice.
4. Put the reference-image path into `skills/digital-human-koubo/persona.json` (`media.reference_image`, or `other_hosts.<name>.reference_image` for a second presenter).

Details: [`references/new-avatar.md`](skills/digital-human-koubo/references/new-avatar.md).

<p align="center"><img src="docs/images/scene-composite.jpg" width="720" alt="Reference photo → composited livestream studio"></p>

---

## Five editing styles

<p align="center"><img src="docs/images/five-styles.jpg" width="820" alt="The five editing styles"></p>

| Style | Ratio | Length | Best for | Template |
|---|---|---|---|---|
| **A** Finance / tech explainer (Xiaolin-style structure) | 16:9 | 3–20 min | events, data, "why…" | `finance-explainer` engine |
| **B** Influencer talking head with animated captions | 9:16 | 30–120 s | product picks, sales, opinions | `templates/huazi-916` (data-driven) |
| **C** Launch breakdown | 16:9 | 30–90 s | new products / models | `templates/reference/launch-169` |
| **D** Step-by-step tutorial | 16:9 | 3–8 min | "how to…", tool setup | `templates/reference/tutorial-169` |
| **E** Multi-host · multi-language · multi-scene | 16:9 | 3–7 min | capability demos, going global | `templates/reference/multihost-169` |

Style B has three caption intensities — **restrained / standard / lively**:

<p align="center"><img src="docs/images/huazi-presets.jpg" width="820" alt="Caption intensity presets"></p>

Style A learns only the *structure and editing grammar* of popular explainer channels. It never uses a real creator's face, voice, set or lines.

---

## 48 packaging components

We measured 25 videos frame by frame (shot detection, opening beats, on-screen text, sound) — full reports in [`references/research/`](skills/digital-human-koubo/references/research/).

<p align="center"><img src="docs/images/creator-pacing.jpg" width="720" alt="Cuts per minute measured on 25 creator videos"></p>

**Rules distilled from the research** ([`packaging-playbook.md`](skills/digital-human-koubo/references/packaging-playbook.md)):
- Cut count can be low, but stimulation can't stop: in the first 30 s, something new every 3–5 s.
- First 3 s: the claim or the action — no greeting, no logo.
- A BGM bed under everything; sound effects only on events (1–3 per minute in Chinese talking-head channels); 0.6–1.0 s of silence right before a reveal.
- For a single-camera digital human, the cheapest pacing is **punch-in cuts** on sentence boundaries (1.0× / 1.18× / 1.32×).

<p align="center"><img src="docs/images/packaging-gallery.jpg" width="820" alt="Packaging component gallery"></p>

| Group | Components |
|---|---|
| Opening / hooks | TeaserColdOpen · ColdOpenFreeze · SearchTyping · NumberSpike · SlamText · WordStack · TornStrip · **TextBehind** |
| Evidence / data | EvidenceCard · DocFocus · SourceDoc · ZoomFocus · Counter · Odometer · GlassPanel · SpecCard · LineDraw · BarCompare · ReviewCards · ArchiveCards · MapRoute · CompareWipe · PaperCollage |
| Annotation / people | HandDraw · CalloutPill · LeaderLabel · TypedNameTag · LowerThird · NamePlate · SourceTag · FreezeFrame |
| Rhythm / interaction | PunchInHost · KeywordStack · RetentionCaption · TiltLine · Aside · Danmaku · ReactionPop · MemeWindow · PollPop · GlitchInterstitial · HostFloaters · ProgressChapters · ProgressTracker · ChapterCard · RecapBoard · Countdown · GhostWord |

Every component is called by name in a `pack` list, with timings written as `"segment:word"` (e.g. `"3:积分"`), and adapts to 9:16 automatically:

```json
"pack": [
  { "use": "NumberSpike", "at": "1:不到十块钱", "until": "1:end", "text": "¥9.9/节", "label": "一节课" },
  { "use": "Danmaku", "items": [{ "t": "真的假的？", "at": "1:" }, { "t": "AI 还能帮我干活？", "at": "1:教你", "hot": true }] },
  { "use": "TextBehind", "src": "main.mp4", "cutout": "main_cut_s4.webm", "cutoutFrom": 17.2, "at": "4:", "until": "4:end",
    "mode": "count", "lines": [{ "t": "¥99", "font": "en", "color": "#FFE14D", "size": 0.17 }], "count": { "from": 999, "to": 99, "prefix": "¥" } }
]
```
Reference: [`references/packaging.md`](skills/digital-human-koubo/references/packaging.md). Validate before rendering: `python3 scripts/check_edit.py <project>/src`.

### Text behind the presenter

<p align="center"><img src="docs/images/text-behind-layers.jpg" width="760" alt="Original → Vision matte → original + big text + cut-out presenter"></p>

```bash
python3 scripts/cutout_video.py public/main.mp4 public/main_cut_s4.webm --from 17.2 --to 22.4   # matte only the seconds you need
```
It works on **medium shots with headroom**. In a selfie close-up the person fills ~89 % of the frame and hides the text — the script warns above 60 %. Mark such segments `"shot": "depth"` and they are generated as medium shots.

<p align="center"><img src="docs/images/closeup-vs-medium.jpg" width="560" alt="Close-up (89%) hides the text, medium shot (57%) shows it"></p>

---

## Cost reference (measured on the Dreamina channel)

| Video | Generation | Jimeng credits |
|---|---|---|
| **Finance explainer, 16:9, ~96 s (real run in this repo, H3 presenter)** | nano-banana outpaint + 6 H3 beats (480p, 54.8 s) | **≈840 apiz credits** |
| Livestream ad, 9:16, 27 s (converted, H3 480p) | 1 scene image + 5 talking segments | **≈420 apiz credits** |
| 4-minute tutorial, 16:9 (converted) | ~30 talking segments + scene images | **≈1,100** |

Price basis (measured 2026-10): **MiniMax-H3** 480p **12 apiz credits/s** + a flat 7 per call (768P 18/s, 1080p 28/s); nano-banana-pro outpainting ≈60 credits/image; script verification ≈10 credits/segment. The Dreamina fallback channel bills per use (**not free**). Always confirm with the agent's live quote.

## Repository structure

```
skills/
  digital-human-koubo/            main skill
    SKILL.md                      workflow the agent follows
    persona.json                  presenters, reference images, channel configs, prompt templates
    references/                   style menu · packaging · playbook · install · research reports
    scripts/                      build_plan · generate_segments · tts · assemble · align
                                  rangedl · check_edit · cutout_video · voicefx/unify
                                  doctor · new_edit · make_assets
    templates/
      huazi-916/                  9:16 data-driven talking-head template (edit.json)
      packaging/                  48-component kit + gallery project
      reference/                  launch-169 · tutorial-169 · multihost-169
    assets/                       style previews · packaging gallery · avatar reference
  finance-explainer/              Style A engine (episode.json beat sheet, dreamina_beats, narrate_edge, research helpers)
docs/                             README images, GIF previews, posters
```

## Known pitfalls (all handled by the skill)

- Seedance occasionally **burns subtitles** into landscape clips even when told not to → frame check + re-shoot that segment (apiz also offers a subtitle-erase model as a rescue).
- `multimodal2video` does **not** follow the reference image's aspect ratio (defaults to 16:9) → `dreamina_beats.py` / `build_plan.py` pass `--ratio` automatically.
- `seedance2.0fast`'s free queue can stretch for hours at peak time → always use `seedance2.0mini` (its dedicated queue is virtually empty).
- whisper writes Chinese numbers as digits (九百九十九 → 999), so accuracy drops but the line is correct; on the Dreamina channel we default to `apiz align` verification (zero misreads measured).
- Always mute the presenter video track; doubled audio a few ms apart sounds harsh (comb filtering).
- Expo easing never quite reaches the target (99.9 → rounds to 100) → counters snap to the exact value at the end.
- On Windows, never pipe Remotion's output into `| head`-style commands — closing the pipe early kills the render.

## Responsible use

- Use only your own face/voice or ones you have **explicit permission** to use. Never impersonate a real person or creator.
- Every video carries an "AI digital human" label; scene and animal clips are marked "AI generated".
- No made-up numbers, prices, offers or reviews — sample data on screen must be labelled as such.
- Don't use web memes, film/TV stills or celebrity images — the meme components use original stickers generated from your own presenter.
- Credits are spent only after you approve the quote (generation scripts dry-run without `--yes`).

## License & third-party

- Code and docs: [MIT](LICENSE) © 2026 Berryxia (andyhuo520).
- **[Remotion](https://www.remotion.dev/)** is used for rendering and has its own license: free for individuals and companies of up to 3 people; larger companies need a [company license](https://www.remotion.pro/).
- Generation runs on the official **即梦 (Dreamina)** CLI with your own Jimeng account credits; **apiz.ai** (alignment / TTS / voice cloning) uses your own API key; **edge-tts** (narration placeholder) is a Python wrapper around a Microsoft public service — usage and content compliance follow each service's terms.
- Animated emoji: [Google Noto Emoji Animation](https://googlefonts.github.io/noto-emoji-animation/) (CC BY 4.0) — credit "Animated emoji: Google Noto" in your videos.
- Maps: [world-atlas](https://github.com/topojson/world-atlas) (ISC; data from Natural Earth, public domain) · [d3-geo](https://github.com/d3/d3-geo), [topojson-client](https://github.com/topojson/topojson-client) (ISC). For maps involving China's borders in formally published content, check against applicable local standards.
- Speech recognition (optional): [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (MIT).
- Course screenshots in the WorkBuddy demo come from the author's own course. Demo videos are the author's own work; please don't re-upload them as your own.

See [THIRD_PARTY.md](THIRD_PARTY.md) for details.

---

<div align="center">

Made by **Berryxia** · built with Claude Code · if this helped, a ⭐ helps others find it.

</div>
