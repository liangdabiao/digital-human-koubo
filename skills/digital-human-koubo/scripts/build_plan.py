#!/usr/bin/env python3
"""口播稿 → 生成计划 plan.json（即梦 dreamina CLI 三通道）+ 费用报价。

用法：
  python3 build_plan.py script.json plan.json [--purpose "..."] [--host tank]
                      [--channel default|long|audio_ref] [--reference 图片路径] [--all-720p]

script.json 段格式（与旧版兼容，新增可选字段）：
  [{"id": "s1", "shot": "full|pip|vlog|depth", "t": "这一段要念的台词",
    "host": "tank|me|cat|dog",            # 不写 = tank（persona 主数字人）
    "lang": "zh|en|ja|...",               # 不写 = zh；外语段台词直接写目标语言
    "channel": "default|long|audio_ref",  # 不写 = --channel 参数（默认 default）
    "audio": "gen/tts/s3.mp3"}]           # channel=audio_ref 时必填（先跑 tts.py）

- 段长：中文 = ceil(去标点字数/5.4 + 1.0)，夹在 [4, 通道上限]；audio_ref 段 = 音频实长 + 0.3
- 超过通道上限会报错：把台词拆短，或该段标 "channel": "long"（seedance2.5 最长 30 秒）
- 输出 plan.json（generate_segments.py 的输入）并打印报价：段数 · 秒数 · 预估积分 · 即梦余额
报价只是预估；提交后以 dreamina 返回的 credit_count 为准。**先报价、用户确认后才跑 generate_segments.py。**
"""
import json, math, re, subprocess, sys, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
P = json.loads((HERE / "persona.json").read_text(encoding="utf-8"))

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def has(name):
    return name in sys.argv

def clean_zh(t):
    return re.sub(r"[\s，。、：；！？,.:;!?“”\"（）()《》…·—-]", "", t)

def estimate_seconds(t, lang):
    if lang.startswith("zh"):
        return math.ceil(len(clean_zh(t)) / P["voice"]["speed_cps"] + 1.0)
    if re.search(r"[\u3040-\u30ff\uac00-\ud7af]", t):          # 日/韩：约 7 字/秒
        return math.ceil(len(re.sub(r"\s", "", t)) / 7 + 1.0)
    return math.ceil(len(t.split()) / 2.6 + 1.0)               # 拉丁/阿拉伯：约 2.6 词/秒

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def image_ratio(path):
    """multimodal2video 不会跟随参考图比例（默认 16:9），必须显式给。"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        w, h = map(int, r.stdout.strip().split(","))
    except ValueError:
        return "9:16"
    return "9:16" if h > w else ("16:9" if w > h else "1:1")

def dreamina_balance():
    exe = shutil.which("dreamina") or str(Path.home() / "bin" / ("dreamina.exe" if sys.platform == "win32" else "dreamina"))
    if not Path(exe).exists():
        return None
    try:
        r = subprocess.run([exe, "user_credit"], capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout).get("total_credit")
    except Exception:
        return None

def build_prompt(s, ch, host_key, purpose):
    act = P["acts"].get(s.get("shot", "full"), P["acts"]["full"])
    lang = P["language_names"].get(s.get("lang", "zh"), s.get("lang", "zh"))
    host = P["other_hosts"].get(host_key, {}) if host_key != "tank" else {}
    look = host.get("look", P["look"])
    voice_desc = host.get("voice_desc", P["voice"]["desc"])
    tpl = (P["prompt_template_audio_ref"] if ch == "audio_ref"
           else (P["prompt_template_landscape"] if host.get("ratio") == "16:9" else P["prompt_template"]))
    return tpl.format(look=look, purpose=purpose, act=act, language=lang,
                      line=s["t"], voice_desc=voice_desc)

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    purpose = arg("--purpose", "带货主播介绍福利")
    host_default = arg("--host", "tank")
    channel_default = arg("--channel", "default")
    reference_override = arg("--reference")
    S = json.loads(src.read_text(encoding="utf-8"))

    plans, total_credit, total_secs, unknown_price = [], 0, 0.0, 0
    for s in S:
        ch_name = s.get("channel", channel_default)
        ch = P["channels"][ch_name]
        host_key = s.get("host", host_default)
        ref = reference_override or (P["other_hosts"].get(host_key, {}).get("reference_image")
                                     if host_key != "tank" else None) or P["media"]["reference_image"]
        if not (HERE / ref).exists() and not Path(ref).exists():
            sys.exit(f"{s['id']}: 参考图不存在：{ref}（先按 references/new-avatar.md 做形象）")

        if ch_name == "audio_ref":
            audio = s.get("audio") or f"gen/tts/{s['id']}.mp3"
            if not Path(audio).exists():
                sys.exit(f"{s['id']}: 音频不存在：{audio}（先跑 python3 scripts/tts.py）")
            d = min(ch["max_seconds"], max(ch["min_seconds"], math.ceil(probe_duration(audio) + 0.3)))
        else:
            d = estimate_seconds(s["t"], s.get("lang", "zh"))
            if d > ch["max_seconds"]:
                sys.exit(f"{s['id']} 约 {d} 秒，超过 {ch['model']} 上限 {ch['max_seconds']} 秒：拆成两段，或标 \"channel\": \"long\"")
            d = max(ch["min_seconds"], d)

        rate = ch.get("credit_per_second")
        if rate is None:
            unknown_price += d
        else:
            total_credit += d * rate
        total_secs += d
        plans.append({
            "id": s["id"], "t": s["t"], "shot": s.get("shot", "full"), "lang": s.get("lang", "zh"),
            "channel": ch_name, "command": ch["command"], "model": ch["model"],
            "resolution": ch["resolution"], "duration": d,
            "reference_image": str(Path(ref) if Path(ref).exists() else HERE / ref),
            "ratio": image_ratio(ref if Path(ref).exists() else HERE / ref) if ch_name == "audio_ref" else None,
            "audio": s.get("audio") if ch_name == "audio_ref" else None,
            "prompt": build_prompt(s, ch_name, host_key, purpose),
            "est_credit": d * rate if rate is not None else None,
        })

    dst.write_text(json.dumps({"purpose": purpose, "segments": plans}, ensure_ascii=False, indent=1), encoding="utf-8")
    bal = dreamina_balance()
    bal_s = f" · 即梦余额 {bal:g}" if bal is not None else ""
    warn = f"（另有 {unknown_price}s 所在通道单价未实测，提交前先拍 4s 校准）" if unknown_price else ""
    print(f"{len(plans)} 段 · 口播约 {total_secs:g} 秒 · 预估 {total_credit:g} 即梦积分{warn}{bal_s}")
    print(f"计划已写 {dst}。向用户报这一行，等确认后再跑：python3 scripts/generate_segments.py {dst} --yes")

if __name__ == "__main__":
    main()
