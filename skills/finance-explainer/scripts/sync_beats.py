#!/usr/bin/env python3
"""口型同步修复：出镜拍直接采用原生片段自带的音轨（即梦生成的口型与它自己的音频严格对应），
丢弃「另铺 TTS 音轨 + offset 猜测」的做法。

用法：
  python3 sync_beats.py <episode.json> <voice目录> <gen目录> [--public <engine>/public] [--gap 0.18]

做法（每出一个镜拍）：
  1. 抽取原生片段音轨 → voice/audio/<id>.wav（覆盖 TTS 版；口型与这条音频在即梦侧天然同步）
  2. apiz upload（免费）+ apiz align 台词 → 该音频的真实字级时间（≈10 apiz 积分/拍）
  3. 只裁首尾：音频从首字前 0.06s 到末字后 0.25s，画面用同样窗口裁 → <public>/host/host_<id>.mp4
     （裁过的画面与声音仍是一对，sync 不受影响）
  4. 按裁后音频实长重建 timings.json（游标规则与 build_timeline 一致：start 累加 adur + 0.18）
     host 拍的字级时间来自 apiz align；off 拍保留 TTS 音频与词级，仅平移到新游标。
  5. host.json：offset=0（原生一对，无需补偿）。

依赖：apiz CLI（核验 10 积分/拍）、ffmpeg。跑完重新 build_timeline → 渲染即可。
"""
import difflib, json, re, shutil, subprocess, sys, wave
from pathlib import Path

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

CUE_RE = re.compile(r"\[\[([a-z][a-z0-9_-]*)\]\]")
PUNCT = set("，。！？；：、,.!?;:（）()「」『』“”\"'《》…—- 　\n")

def apiz():
    exe = shutil.which("apiz")
    if not exe: sys.exit("找不到 apiz CLI")
    return exe

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def dur(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout.strip())

def clean_text(narration):
    cues = {m.group(1): None for m in CUE_RE.finditer(narration)}
    return CUE_RE.sub("", narration), cues

def align_audio(text, wav, out_json):
    up = sh([apiz(), "upload", str(wav)])
    url = json.loads(up.stdout)["public_url"]
    r = sh([apiz(), "align", text, "--audio", url, f"--output-file={out_json}", "--wait-timeout", "4m"])
    d = json.loads(Path(out_json).read_text(encoding="utf-8")) if Path(out_json).exists() else None
    if not d:
        sys.exit(f"align 失败：{(r.stdout + r.stderr)[-300:]}")
    words = []
    for u in d.get("utterances", []):
        for w in u.get("words", []):
            if w["text"].strip():
                words.append({"w": w["text"], "start": w["start_time"] / 1000, "end": w["end_time"] / 1000})
    heard = "".join(w["w"] for w in words)
    cl = lambda s: re.sub(r"[\s，。、：；！？,.:;!?“”\"（）()《》…·—-]", "", s)
    ratio = difflib.SequenceMatcher(None, cl(text), cl(heard)).ratio()
    return words, ratio

def words_to_chars(words, text):
    """把 align 的词序列按顺序映射回原文，输出每个字的开始秒（缺失处线性内插）。"""
    chars = [None] * len(text)
    ptr = 0
    for w in words:
        wtxt = "".join(c for c in w["w"] if c not in PUNCT)
        if not wtxt: continue
        while ptr < len(text) and text[ptr] in PUNCT: ptr += 1
        if text.startswith(wtxt, ptr):
            span = max(1, len(wtxt))
            for k in range(len(wtxt)):
                if ptr + k < len(text) and chars[ptr + k] is None:
                    chars[ptr + k] = w["start"] + (w["end"] - w["start"]) * k / span
            ptr += len(wtxt)
    known = [(i, v) for i, v in enumerate(chars) if v is not None]
    for i in range(len(chars)):
        if chars[i] is None:
            prev = max([k for k, v in known if k < i], default=None)
            nxt = min([k for k, v in known if k > i], default=None)
            if prev is None and nxt is None: chars[i] = words[0]["start"] if words else 0.0
            elif prev is None: chars[i] = max(0.0, chars[nxt] - 0.12 * (nxt - i))
            elif nxt is None: chars[i] = chars[prev] + 0.18 * (i - prev)
            else: chars[i] = chars[prev] + (chars[nxt] - chars[prev]) * (i - prev) / (nxt - prev)
    return chars

def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    ep = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    voice = Path(sys.argv[2]); gen = Path(sys.argv[3])
    public = Path(arg("--public")) if arg("--public") else None
    GAP = float(arg("--gap", "0.18"))
    tim_p = voice / "timings.json"
    old = json.loads(tim_p.read_text(encoding="utf-8"))
    clips = json.loads((gen / "clips.json").read_text(encoding="utf-8"))
    align_dir = voice / "align"; align_dir.mkdir(exist_ok=True)
    if public: (public / "host").mkdir(parents=True, exist_ok=True)

    new_beats, cursor = {}, 0.0
    for b in ep["beats"]:
        bid = b["id"]
        if b.get("kind") == "chapter":
            new_beats[bid] = old["beats"][bid]; continue
        if bid not in clips:
            ob = dict(old["beats"][bid])                       # off 拍：保留 TTS 音频与词级，平移游标
            shift = cursor - ob["start"]
            ob["start"] = round(cursor, 3); ob["end"] = round(cursor + ob["duration"], 3)
            ob["words"] = [{**w, "start": round(w["start"] + shift, 3), "end": round(w["end"] + shift, 3)} for w in ob["words"]]
            ob["chars"] = [round(c + shift, 3) for c in ob["chars"]]
            ob["cues"] = {k: round(v + shift, 3) for k, v in ob["cues"].items()}
            new_beats[bid] = ob
            cursor += ob["duration"] + GAP
            continue
        text, _ = clean_text(b["narration"])
        raw = Path(clips[bid])
        raw_dur = dur(raw)
        tmp = voice / f"_{bid}_raw.wav"
        sh(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-vn", "-ac", "1", "-ar", "16000", str(tmp)])
        words, ratio = align_audio(text, tmp, align_dir / f"{bid}.json")
        if not words: sys.exit(f"{bid}: align 没有词产出")
        s0 = max(0.0, words[0]["start"] - 0.06)
        e1 = min(raw_dur, words[-1]["end"] + 0.25)
        # 裁画面与声音（同窗口，原生一对）
        if public:
            sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s0:.3f}", "-to", f"{e1:.3f}", "-i", str(raw),
                "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                str(public / "host" / f"host_{bid}.mp4")])
        sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s0:.3f}", "-to", f"{e1:.3f}", "-i", str(raw),
            "-vn", "-ac", "1", "-ar", "16000", str(voice / "audio" / f"{bid}.wav")])
        tmp.unlink(missing_ok=True)
        adur = dur(voice / "audio" / f"{bid}.wav")
        rel_words = [{"text": w["w"], "start": round(cursor + max(0.0, w["start"] - s0), 3),
                      "end": round(cursor + min(adur, w["end"] - s0), 3)} for w in words]
        chars_rel = words_to_chars(words, text)
        cues = {m.group(1): m.start() for m in CUE_RE.finditer(b["narration"])}
        new_beats[bid] = {
            "file": f"audio/{bid}.wav", "text": text,
            "start": round(cursor, 3), "end": round(cursor + adur, 3), "duration": round(adur, 3),
            "words": rel_words, "chars": [round(cursor + c, 3) for c in chars_rel],
            "cues": {k: round(cursor + chars_rel[min(v, len(chars_rel) - 1)], 3) for k, v in cues.items() if v < len(chars_rel)},
            "align": round(ratio, 3)}
        n = len([c for c in text if c not in PUNCT and not c.isspace()])
        print(f"{'⚠ ' if ratio < 0.85 else ''}{bid:5s} 片内语音起点 {words[0]['start']:5.2f}s → 裁 [{s0:.2f},{e1:.2f}]  "
              f"拍长 {adur:5.2f}s  {n / adur:4.1f} 字/秒  对齐 {ratio:.0%}")
        cursor += adur + GAP

    tim = {"beats": new_beats, "gap": GAP, "lead": 0.0, "total": round(max(0.0, cursor - GAP), 3)}
    tim_p.write_text(json.dumps(tim, ensure_ascii=False, indent=1), encoding="utf-8")
    if public:
        host = {"src": "assets/anchor.png", "kind": "image", "face": [0.5, 0.33], "offset": 0.0,
                "clips": {bid: {"src": f"host/host_{bid}.mp4", "offset": 0.0} for bid in clips
                          if (public / "host" / f"host_{bid}.mp4").exists()}}
        (Path(arg("--host-out", "host.json"))).write_text(json.dumps(host, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ host.json（offset=0：画面与声音本就是同一条原生素材）")
    print(f"→ {tim_p}  total {tim['total']}s。下一步：build_timeline → 渲染")

if __name__ == "__main__":
    main()
