#!/usr/bin/env python3
"""旁白占位：edge-tts（免费）+ 原生词级时间戳，输出与 narrate_mimo / grok_beats 同一套 timings.json 契约。

用法：
  python3 narrate_edge.py <narration.json> <输出目录> [--gap 0.22] [--lead 0.3] [--voice 女声|<edge音色id>] [--rate +0%]

narration.json：{"voice": {"engine": "edge", "voice": "女声"}, "lexicon": {"GPU": "G P U", ...},
                 "beats": [{"id": "c01", "narration": "…[[cue]]…"}]}
- 音色：女声=zh-CN-XiaoxiaoNeural，男声=zh-CN-YunxiNeural，或直接写 edge-tts 音色 id；命令行 --voice 优先
- lexicon：合成前替换（型号/缩写写中文读法）；cue 用 [[name]] 标，进 timings.cues（绝对秒）
- 逐词时间来自 edge-tts 的 WordBoundary 事件（TTS 念的就是给定文本，天然全对齐，不需要 whisper）
- 输出：<out>/audio/<id>.wav（16k 单音）、<out>/narration.wav（带 gap/lead 的整条）、<out>/timings.json
依赖：pip install edge-tts；ffmpeg。
"""
import asyncio, json, re, subprocess, sys, wave
from pathlib import Path

import numpy as np

SR = 16000
CUE_RE = re.compile(r"\[\[([a-z][a-z0-9_-]*)\]\]")
PUNCT = set("，。！？；：、,.!?;:（）()「」『』“”\"'《》…—- 　\n")
VOICES = {"女声": "zh-CN-XiaoxiaoNeural", "男声": "zh-CN-YunxiNeural"}

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def synth(text, voice, rate):
    """一次流式调用同时拿 mp3 字节和 WordBoundary 词级事件。"""
    import edge_tts
    audio, words = bytearray(), []
    async def run():
        c = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        async for ch in c.stream():
            if ch["type"] == "audio":
                audio.extend(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"text": ch["text"], "start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7})
    asyncio.run(run())
    return bytes(audio), words

def spoken_map(clean, lexicon):
    """把 lexicon 应用到 clean，返回 (spoken文本, spoken每字对应的clean字符下标)。"""
    keys = sorted(lexicon, key=len, reverse=True)
    out, idx, i = [], [], 0
    while i < len(clean):
        for k in keys:
            if k and clean.startswith(k, i):
                for ch in lexicon[k]:
                    if not ch.isspace():
                        out.append(ch); idx.append(i)
                i += len(k); break
        else:
            if not clean[i].isspace():
                out.append(clean[i]); idx.append(i)
            i += 1
    return "".join(out), idx

def words_to_orig(words, spoken, sp2orig, clean):
    """把 WordBoundary 词映射回 clean 的字符区间（i0,i1）。"""
    res, ptr = [], 0
    for w in words:
        wtxt = "".join(ch for ch in w["text"] if not ch.isspace())
        if not wtxt:
            continue
        while ptr < len(spoken) and spoken[ptr] != wtxt[0] and spoken[ptr] in PUNCT:
            ptr += 1                                   # 跳过标点
        if spoken.startswith(wtxt, ptr):
            a, b = sp2orig[ptr], sp2orig[ptr + len(wtxt) - 1]
            res.append({"text": wtxt, "start": w["start"], "end": w["end"], "i0": a, "i1": b + 1})
            ptr += len(wtxt)
        else:                                          # 兜底：顺序放一个词
            if ptr < len(sp2orig):
                res.append({"text": wtxt, "start": w["start"], "end": w["end"], "i0": sp2orig[ptr], "i1": sp2orig[ptr] + 1})
                ptr += 1
    chars = [None] * len(clean)
    for w in res:
        span = max(1, w["i1"] - w["i0"])
        for k in range(w["i0"], min(w["i1"], len(clean))):
            if chars[k] is None:
                chars[k] = w["start"] + (w["end"] - w["start"]) * (k - w["i0"]) / span
    known = [(i, v) for i, v in enumerate(chars) if v is not None]
    for i in range(len(chars)):
        if chars[i] is None:
            prev = max([k for k, v in known if k < i], default=None)
            nxt = min([k for k, v in known if k > i], default=None)
            if prev is None and nxt is None: chars[i] = w["start"] if res else 0.0
            elif prev is None: chars[i] = max(0.0, chars[nxt] - 0.12 * (nxt - i))
            elif nxt is None: chars[i] = chars[prev] + 0.18 * (i - prev)
            else: chars[i] = chars[prev] + (chars[nxt] - chars[prev]) * (i - prev) / (nxt - prev)
    return res, chars

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    nj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2]); (out / "audio").mkdir(parents=True, exist_ok=True)
    gap, lead = float(arg("--gap", "0.22")), float(arg("--lead", "0.3"))
    vcfg = nj.get("voice", {})
    voice = arg("--voice") or vcfg.get("voice", "女声")
    voice = VOICES.get(voice, voice)
    rate = arg("--rate", "+0%")
    lex = nj.get("lexicon", {})

    timings = {"beats": {}, "gap": gap, "lead": lead}
    cursor = lead
    for b in nj["beats"]:
        cues = {m.group(1): m.start() for m in CUE_RE.finditer(b["narration"])}
        clean = CUE_RE.sub("", b["narration"])
        spoken, sp2orig = spoken_map(clean, lex)
        mp3, words = synth(spoken, voice, rate)
        tmp = out / f"_{b['id']}.mp3"; tmp.write_bytes(mp3)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-ac", "1", "-ar", str(SR), str(out / "audio" / f"{b['id']}.wav")], check=True)
        tmp.unlink()
        dur = (len(mp3)) and float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / "audio" / f"{b['id']}.wav")], capture_output=True, text=True).stdout)
        wlist, chars = words_to_orig(words, spoken, sp2orig, clean)
        abs_chars = [round(cursor + c, 3) for c in chars]
        timings["beats"][b["id"]] = {
            "file": f"audio/{b['id']}.wav", "text": clean,
            "start": round(cursor, 3), "end": round(cursor + dur, 3), "duration": round(dur, 3),
            "words": [{"text": w["text"], "start": round(cursor + w["start"], 3), "end": round(cursor + w["end"], 3), "i0": w["i0"], "i1": w["i1"]} for w in wlist],
            "chars": abs_chars,
            "cues": {k: round(cursor + chars[min(v, len(chars) - 1)], 3) for k, v in cues.items() if v < len(chars)},
            "align": 1.0}
        n = len([c for c in clean if c not in PUNCT and not c.isspace()])
        print(f"{b['id']:6s} {dur:5.2f}s  {n / dur:4.1f} 字/秒  词 {len(wlist)}")
        cursor += dur + gap
    timings["total"] = round(max(0.0, cursor - gap), 3)
    # 整条 narration.wav
    segs, total = [], timings["total"] + 0.5
    buf = np.zeros(int(total * SR), dtype=np.float32)
    for b in nj["beats"]:
        t = timings["beats"][b["id"]]
        raw = wave.open(str(out / t["file"]), "rb")
        pcm = np.frombuffer(raw.readframes(raw.getnframes()), np.int16).astype(np.float32) / 32768.0
        raw.close()
        i0 = int(t["start"] * SR)
        buf[i0:i0 + len(pcm)] += pcm[:max(0, len(buf) - i0)]
    with wave.open(str(out / "narration.wav"), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(np.clip(buf * 32767, -32768, 32767).astype(np.int16).tobytes())
    (out / "timings.json").write_text(json.dumps(timings, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {out / 'timings.json'}  total {timings['total']}s（{voice}，免费）")

if __name__ == "__main__":
    main()
