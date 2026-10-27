#!/usr/bin/env python3
"""逐段质检 → 剪掉段尾空白 → 统一规格 → 拼接。（即梦版：gen/<id>.mp4）

用法：python3 assemble.py script.json gen/manifest.json [--out 成片_完整版.mp4] [--qc align|whisper|none] [--lang zh] [--size 宽x高]
- script.json：和 build_plan.py 同一份；manifest.json：generate_segments.py 产出（或兼容旧版 ids.json）
- --qc align（默认）：apiz align 核验台词 + 拿字级时间戳（≈10 积分/段，**要 --yes 确认**）——
  2026-10 实测代替 whisper 回听：零安装、零漏识别，还能直接出打轴数据
- --qc whisper：本地 whisper-cli 回听（零积分，要装 whisper.cpp + 模型）
- --qc none：跳过核验，整段保留（快速预览用）
- 输出 cut/<id>.mp4（30fps、48k 立体声）、cut/words/<id>.json（统一词级时间，align.py 用）、
  cut/qa.json、cut/list.txt、拼接好的 --out（-16 LUFS）
- 准确率 < 85% 的段打 ⚠：先人工听/看，真念错就用 apiz seedance2.5 局部重拍或 generate_segments.py --only 重拍那段
"""
import json, subprocess, difflib, re, sys, shutil
from pathlib import Path

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
S = json.load(open(a[0], encoding="utf-8"))
IDS_RAW = json.load(open(a[1], encoding="utf-8"))
opt = lambda k, d: a[a.index(k) + 1] if k in a else d
out_name = opt('--out', '成片_完整版.mp4')
qc_mode = opt('--qc', 'align')
lang = opt('--lang', 'zh')
size = opt('--size', '')
YES = '--yes' in a

def seg_file(sid):
    m = IDS_RAW.get(sid)
    if isinstance(m, dict): return m["file"]            # 新版 manifest
    return f"gen/renoise-{m}.mp4"                        # 旧版 ids.json 兼容

def clean(s): return re.sub(r'[\s，。、：；！？,.:;!?“”\"（）()《》…·—-]', '', s).lower()

def apiz():
    exe = shutil.which("apiz")
    if not exe: sys.exit("找不到 apiz CLI：apiz auth login 或见 references/install.md")
    return exe

def qc_align(sid, text, src, wav):
    """apiz align：上传音频 → 与台词对齐 → 统一词级时间（秒）。返回 (acc, speech_end, heard)"""
    up, _ = subprocess.run([apiz(), "upload", wav], capture_output=True, text=True, check=True), None
    url = json.loads(up.stdout)["public_url"]
    out_p = Path(f"qc/{sid}.align.json"); out_p.parent.mkdir(exist_ok=True)
    r = subprocess.run([apiz(), "align", text, "--audio", url, f"--output-file={out_p}",
                        "--wait-timeout", "4m"], capture_output=True, text=True)
    d = json.loads(out_p.read_text(encoding="utf-8")) if out_p.exists() else None
    if not d: sys.exit(f"{sid}: align 失败：{(r.stdout + r.stderr)[-400:]}")
    words = []
    for u in d.get("utterances", []):
        for w in u.get("words", []):
            if w["text"].strip():
                words.append({"w": w["text"], "start": round(w["start_time"] / 1000, 3),
                              "end": round(w["end_time"] / 1000, 3)})
    heard = ''.join(w["w"] for w in words)
    acc = difflib.SequenceMatcher(None, clean(text), clean(heard)).ratio()
    speech_end = max((w["end"] for w in words), default=0.0)
    Path("cut/words").mkdir(exist_ok=True)
    json.dump({"id": sid, "engine": "align", "words": words}, open(f"cut/words/{sid}.json", "w", encoding="utf-8"), ensure_ascii=False)
    return acc, speech_end, heard

def qc_whisper(sid, src, wav, lg):
    """本地 whisper-cli 回听（原版逻辑）。"""
    WM = __import__('os').environ.get('WHISPER_MODEL') or str(Path.home() / "models" / "ggml-medium-q5_0.bin")
    cmd = ['whisper-cli', '-m', WM, '-l', lg] + (['--prompt', '以下是普通话的句子。', '-ml', '1'] if lg == 'zh' else []) + ['-oj', '-of', f'cut/words/{sid}_w', '-f', wav]
    subprocess.run(cmd, capture_output=True)
    tj = json.load(open(f'cut/words/{sid}_w.json', errors='replace'))['transcription']
    words = [{"w": t['text'].strip(), "start": t['offsets']['from'] / 1000, "end": t['offsets']['to'] / 1000}
             for t in tj if t['text'].strip() and not t['text'].strip().startswith('[')]
    heard = ''.join(w["w"] for w in words)
    acc = 0.0
    Path("cut/words").mkdir(exist_ok=True)
    json.dump({"id": sid, "engine": "whisper", "words": words}, open(f"cut/words/{sid}.json", "w", encoding="utf-8"), ensure_ascii=False)
    return acc, max((w["end"] for w in words), default=0.0), heard

Path('cut').mkdir(exist_ok=True)
if qc_mode == 'align' and not YES:
    n = len(S)
    sys.exit(f"align QC 将对 {n} 段跑 apiz align，预计 ≈{n * 10} 积分（0.1 元）。确认后加 --yes 重跑；不想花钱用 --qc whisper（要装 whisper-cli）或 --qc none。")

rep = []
for s in S:
    sid = s['id']; src = seg_file(sid); wav = f'cut/{sid}.wav'
    lg = s.get('lang_code', s.get('lang', lang))
    if lg in ('en', 'ja', 'ko', 'fr', 'es', 'ar'): lg = {'en': 'en', 'ja': 'ja', 'ko': 'ko', 'fr': 'fr', 'es': 'es', 'ar': 'ar'}.get(lg, 'zh')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-ar', '16000', '-ac', '1', wav], check=True)
    if qc_mode == 'align':
        acc, speech_en, heard = qc_align(sid, s['t'], src, wav)
    elif qc_mode == 'whisper':
        acc, speech_en, heard = qc_whisper(sid, src, wav, lg)
    else:
        acc, speech_en, heard = 1.0, None, ''
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split(','))
    sz = size or f'{w - w % 2}x{h - h % 2}'          # 保持源尺寸（即梦 9:16 720p 是 720×1280）
    keep = min(dur, speech_en + 0.25) if speech_en else dur
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-t', f'{keep:.3f}', '-vf', f'scale={sz.replace("x", ":")}:flags=lanczos,fps=30,format=yuv420p',
                    '-af', f'aresample=48000,afade=t=out:st={max(0, keep - 0.12):.3f}:d=0.12', '-ac', '2', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', f'cut/{sid}.mp4'], check=True)
    rep.append(dict(id=sid, acc=round(acc, 3), speech=[0, round(speech_en, 2)] if speech_en else None,
                    keep=round(keep, 2), src_dur=round(dur, 2), heard=heard))
    print(f"{'⚠' if acc < 0.85 else ' '}{sid:6s} 准确率 {acc:.0%}  说到 {speech_en:.2f}s" if speech_en else f"{' '}{sid:6s} 跳过核验",
          f" 保留 {keep:.2f}/{dur:.2f}s")
json.dump(rep, open('cut/qa.json', 'w', encoding="utf-8"), ensure_ascii=False, indent=1)
open('cut/list.txt', 'w', encoding="utf-8").write(''.join(f"file '{s['id']}.mp4'\n" for s in S))
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'cut/list.txt', '-c', 'copy', 'cut/joined.mp4'], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'cut/joined.mp4', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out_name], check=True)
print('拼接完成', out_name, round(sum(r['keep'] for r in rep), 2), '秒  →  下一步：python3 scripts/align.py', a[0], '--out <工程>/src/tl.json')
