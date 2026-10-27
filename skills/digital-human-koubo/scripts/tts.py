#!/usr/bin/env python3
"""可选：edge-tts 合成旁白/指定音色音频（通道 C 的音频来源）。

用法：
  python3 tts.py script.json [--outdir gen/tts] [--voice zh-CN-XiaoxiaoNeural] [--rate +0%]

- 只处理标了 "tts": true 的段：[{"id":"s3","t":"台词","tts":true,"voice_key":"zh"}]
  voice_key 是 persona.json → voice.tts.map 的键（zh/zh-male/en/ja/ko），不写用 --voice 或默认
- 输出 <outdir>/<id>.mp3 + <outdir>/<id>.timing.json（逐词毫秒时间戳，旁白段打轴可直接用）
- 单段超过 15 秒会警告：multimodal2video 的音频参考上限 15 秒（seedance2.5 为 30 秒）
依赖：pip install edge-tts（免费，不走积分）。
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
P = json.loads((HERE / "persona.json").read_text(encoding="utf-8"))

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def synth(text, voice, rate, out_mp3):
    """调 edge-tts CLI；再走 python API 抓 WordBoundary 词级时间戳。"""
    r = subprocess.run([sys.executable, "-m", "edge_tts", "-t", text, "-v", voice,
                        "--rate", rate, "--write-media", str(out_mp3), "--no-progress"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not out_mp3.exists():
        sys.exit(f"edge-tts 合成失败：{r.stderr.strip()[-400:]}")
    try:
        import asyncio, edge_tts
        words = []
        async def collect():
            c = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
            async for chunk in c.stream():
                if chunk["type"] == "WordBoundary":
                    words.append({"w": chunk["text"],
                                  "start": chunk["offset"] / 1e5,      # 100ns → ms
                                  "end": (chunk["offset"] + chunk["duration"]) / 1e5})
        asyncio.run(collect())
        return words
    except ImportError:
        return []   # 只有 CLI 可用时拿不到词级时间戳，不阻塞合成

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    S = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outdir = Path(arg("--outdir", "gen/tts"))
    outdir.mkdir(parents=True, exist_ok=True)
    voice_override = arg("--voice")
    rate = arg("--rate", "+0%")
    vmap = P["voice"]["tts"]["map"]
    todo = [s for s in S if s.get("tts")]
    if not todo:
        print("没有标 tts:true 的段，不需要合成。")
        return
    for s in todo:
        voice = voice_override or vmap.get(s.get("voice_key", "zh"), P["voice"]["tts"]["default"])
        out = outdir / f"{s['id']}.mp3"
        print(f"{s['id']} → {voice} …", end=" ", flush=True)
        words = synth(s["t"], voice, rate, out)
        dur = probe_duration(out)
        (outdir / f"{s['id']}.timing.json").write_text(
            json.dumps({"id": s["id"], "voice": voice, "duration": round(dur, 3), "words": words},
                       ensure_ascii=False), encoding="utf-8")
        warn = "  ⚠ 超过 15 秒：multimodal2video 音频参考上限 15s（2.5 为 30s），拆段或换 long 通道" if dur > 15 else ""
        print(f"{dur:.2f}s{warn}（词级时间戳 {len(words)} 个）")
    print("完成。audio_ref 段接着跑：python3 scripts/build_plan.py …")

if __name__ == "__main__":
    main()
