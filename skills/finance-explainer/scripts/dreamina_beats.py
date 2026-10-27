#!/usr/bin/env python3
"""逐拍生成数字人出镜片段（即梦 dreamina CLI，替代原 Renoise Wan 3.0 / Grok 1.5 两方案）。

用法：
  python3 dreamina_beats.py <episode.json> <voice目录> [--mode audio|native] [--anchor host/anchor.jpg]
                            [--gen gen] [--public <engine>/public] [--host-out host.json]
                            [--yes] [--only c03,c04] [--resubmit]

- audio 模式（默认，对应原 W 方案）：每拍用 voice/audio/<id>.wav（align_recording / narrate_edge / narrate_mimo 产出）
  作音色+口型参考 → multimodal2video，口型跟最终音频逐字同步，成片零换声。mini ≈6 即梦积分/秒。
- native 模式（对应原 G 方案）：台词写进提示词，模型自己配音 → image2video。
  出片后跑 grok_beats.py（喂 clips.json）做逐拍对齐写 host.json，换音色见 production.md。
- 干跑默认；--yes 才提交；--only c03 重拍指定拍；--resubmit 忽略旧任务重交（旧积分不退）。
- 产物 <gen>/host_<id>.mp4 + <gen>/clips.json；audio 模式另写 host.json（offset 默认 0，首拍抽帧校准）。
- 单拍音频 >14 秒：自动升 seedance2.5（VIP，上限 30 秒，单价未实测先拍一条校准）。
"""
import json, math, shutil, subprocess, sys, time
from pathlib import Path

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def has(name):
    return name in sys.argv

def dreamina():
    exe = shutil.which("dreamina") or str(Path.home() / "bin" / ("dreamina.exe" if sys.platform == "win32" else "dreamina"))
    if not Path(exe).exists():
        sys.exit("找不到 dreamina CLI：见 references/install.md（finance 侧同款安装）")
    return exe

def run_json(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(r.stdout), r
    except json.JSONDecodeError:
        return None, r

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def clean_zh(t):
    import re
    return re.sub(r"[\s，。、：；！？,.:;!?“”\"（）()《》…·—-\[\]]", "", t)

AUDIO_PROMPT = ("画面中的主播坐在书房里正对镜头讲话，嘴部始终清晰可见，口型与参考音频的中文语音逐字同步；"
                "说话停顿时嘴巴自然闭合，表情亲切自然、不夸张，偶尔点头、眨眼，双手做解释性手势；"
                "固定机位中景，不推拉，人物长相、发型、服装、场景和光线与参考图完全一致。"
                "参考音频就是她的声音：用参考音频的音色和台词说话。音频：只用参考音频的人声。无字幕、无文字、无水印。")

NATIVE_PROMPT = ("固定机位中景，书房场景，不推拉，人物长相、发型、服装、场景和光线与参考图完全一致。"
                 "画面中的主播正对镜头，像亲切的财经解说博主一样看镜头讲话，嘴部始终清晰可见：眼神明亮专注，"
                 "自然眨眼，讲到关键词时偶尔挑眉、微笑、小幅点头，双手做解释性手势。"
                 "她用普通话清晰地说：\"{line}\" 语气亲切自然，语速适中。"
                 "音频：只有她清晰的说话声和安静的房间底噪，没有音乐。无字幕、无文字、无水印。")

def submit(D, beat, mode, anchor, audio, dur):
    if mode == "audio":
        cmd = [D, "multimodal2video", "--prompt", AUDIO_PROMPT, "--image", str(anchor), "--audio", str(audio),
               "--ratio", "16:9", "--duration", str(dur), "--video_resolution", "720p",
               "--model_version", "seedance2.0mini", "--poll", "0"]
    else:
        cmd = [D, "image2video", "--prompt", NATIVE_PROMPT.format(line=beat["narration"]), "--image", str(anchor),
               "--ratio", "16:9", "--duration", str(dur), "--video_resolution", "720p",
               "--model_version", "seedance2.0mini", "--poll", "0"]
    out, r = run_json(cmd)
    if out is None:
        sys.exit(f"提交失败（非 JSON）：{((r.stdout or '') + (r.stderr or ''))[-500:]}")
    if out.get("gen_status") not in ("querying", "success"):
        msg = json.dumps(out, ensure_ascii=False)
        if "AigcComplianceConfirmationRequired" in msg:
            sys.exit(f"{beat['id']}：模型需先在即梦网页端用一次完成首次确认，再重试。")
        sys.exit(f"{beat['id']} 提交失败：{msg[-500:]}")
    return out

def query(D, sub, download_dir=None):
    cmd = [D, "query_result", f"--submit_id={sub}"]
    if download_dir:
        cmd += [f"--download_dir={download_dir}"]
    out, r = run_json(cmd, timeout=600)
    return out or {"gen_status": "unknown"}

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ep = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    voice = Path(sys.argv[2])
    mode = arg("--mode", "audio")
    anchor = Path(arg("--anchor", "host/anchor.jpg"))
    if not anchor.exists():
        sys.exit(f"定妆照不存在：{anchor}（先按 production.md §1 生成）")
    gen = Path(arg("--gen", "gen")); gen.mkdir(exist_ok=True)
    public = arg("--public")
    tasks_p, clips_p = gen / "tasks.json", gen / "clips.json"
    tasks = json.loads(tasks_p.read_text(encoding="utf-8")) if tasks_p.exists() else {}
    clips = json.loads(clips_p.read_text(encoding="utf-8")) if clips_p.exists() else {}

    only = arg("--only")
    only = set(only.split(",")) if only else None
    beats = [b for b in ep["beats"] if b.get("narration") and b.get("host") != "off"
             and (not only or b["id"] in only)]   # host=off 的拍是纯空镜，不需要出镜片段
    if mode == "audio":
        beats = [b for b in beats if (voice / "audio" / f"{b['id']}.wav").exists()
                 or (voice / "audio" / f"{b['id']}.mp3").exists()]
        missing = [b["id"] for b in ep["beats"] if b.get("narration") and b.get("host") != "off"
                   and b["id"] not in {x["id"] for x in beats} and (not only or b["id"] in only)]
        if missing:
            print(f"⚠ 无音频、跳过（先跑 align_recording.py / narrate_edge.py）：{'、'.join(missing)}")

    plans = []
    for b in beats:
        if mode == "audio":
            ap = voice / "audio" / f"{b['id']}.wav"
            if not ap.exists():
                ap = voice / "audio" / f"{b['id']}.mp3"
            ad = probe_duration(ap)
            if ad > 14:
                model, dur, warn = "seedance2.5", min(30, math.ceil(ad + 1)), "（VIP 通道，单价未实测）"
            else:
                model, dur, warn = "seedance2.0mini", max(4, min(15, math.ceil(ad + 1))), ""
        else:
            ap, model, warn = None, "seedance2.0mini", ""
            dur = max(4, min(15, math.ceil(len(clean_zh(b["narration"])) / 5.2 + 1)))
        plans.append({"beat": b, "audio": ap, "dur": dur, "model": model, "warn": warn})

    est = sum(p["dur"] * 6 for p in plans if p["model"] == "seedance2.0mini")
    est25 = sum(p["dur"] for p in plans if p["model"] == "seedance2.5")
    redo = [p["beat"]["id"] for p in plans if p["beat"]["id"] in clips and not has("--resubmit") and (gen / f"host_{p['beat']['id']}.mp4").exists()]
    todo = [p for p in plans if p["beat"]["id"] not in redo]
    labels = "、".join(f"{p['beat']['id']}({p['dur']}s)" for p in todo)
    print(f"将提交 {len(todo)} 拍（{mode} 模式）：{labels}")
    print(f"预估 {est} 即梦积分" + (f" + {est25}s seedance2.5 未实测" if est25 else "") + " · mini 实测 6 积分/秒")
    if not has("--yes"):
        print("干跑结束。确认后加 --yes 提交。")
        return
    D = dreamina()

    for p in todo:
        bid = p["beat"]["id"]
        if not has("--resubmit") and tasks.get(bid, {}).get("submit_id") and not clips.get(bid):
            print(f"{bid} 复用已有 submit_id {tasks[bid]['submit_id']}")
        else:
            if has("--resubmit"):
                tasks.pop(bid, None)
            print(f"提交 {bid}（{p['model']} {p['dur']}s）{p['warn']}…", flush=True)
            out = submit(D, p["beat"], mode, anchor, p["audio"], p["dur"])
            tasks[bid] = {"submit_id": out["submit_id"], "credits": out.get("credit_count"), "model": p["model"], "dur": p["dur"]}
            tasks_p.write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  submit_id={out['submit_id']}  扣 {out.get('credit_count')} 积分")
        time.sleep(3)

    pending = {b: tasks[b]["submit_id"] for b in tasks if b in {p["beat"]["id"] for p in todo} and not clips.get(b)}
    deadline = time.time() + 1800
    while pending:
        time.sleep(20)
        for bid, sub in list(pending.items()):
            out = query(D, sub)
            if out.get("gen_status") == "success":
                vids = (out.get("result_json") or {}).get("videos") or []
                src = Path(vids[0]["path"]) if vids and vids[0].get("path") and Path(vids[0]["path"]).exists() else None
                if src is None:
                    q = query(D, sub, download_dir=str(gen))
                    vids = (q.get("result_json") or {}).get("videos") or []
                    src = Path(vids[0]["path"]) if vids and vids[0].get("path") and Path(vids[0]["path"]).exists() else None
                if src is None:
                    print(f"  {bid} 下载失败，下轮重试"); continue
                dst = gen / f"host_{bid}.mp4"
                shutil.move(str(src), dst)
                clips[bid] = str(dst)
                clips_p.write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  ✓ {bid} → {dst}")
                pending.pop(bid)
            elif out.get("gen_status") == "fail":
                print(f"  ✗ {bid} 失败：{str(out.get('fail_reason'))[-200:]}（--only {bid} --resubmit 重拍）")
                pending.pop(bid)
            elif time.time() > deadline:
                print(f"  ⏱ {bid} 等待超时，submit_id={sub} 已存，稍后重跑续拉")
                pending.pop(bid)

    if public and mode == "audio":
        (Path(public) / "host").mkdir(parents=True, exist_ok=True)
        host = {"src": str(anchor), "kind": "image", "face": [0.5, 0.33], "offset": 0.0, "clips": {}}
        for p in plans:
            bid = p["beat"]["id"]
            if bid in clips:
                name = f"host/host_{bid}.mp4"
                shutil.copyfile(clips[bid], Path(public) / name)
                host["clips"][bid] = {"src": name, "offset": 0.0}
        host_out = arg("--host-out", "host.json")
        Path(host_out).write_text(json.dumps(host, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ {host_out}（offset 0.0 为预填：拿第一拍截帧对一下口型起点，差几帧改 host.json 的 offset）")
    if mode == "native":
        print(f"下一步：python3 scripts/grok_beats.py {sys.argv[1]} {clips_p} voice --public {public or '<engine>/public'}")

if __name__ == "__main__":
    main()
