#!/usr/bin/env python3
"""按 plan.json 提交即梦（dreamina CLI）生成任务 → 轮询 → 下载 → 校验 → gen/manifest.json。

用法：
  python3 generate_segments.py plan.json            # 干跑：打印将提交的任务和花费，不花钱
  python3 generate_segments.py plan.json --yes      # 用户确认报价后真正提交
  可选：--only s1,s3   --timeout 1800（单段轮询上限秒）   --poll 20（轮询间隔）

- 通道 A/B：image2video（台词写在提示词里，Seedance 原生配音）
- 通道 C：multimodal2video（plan 里带 audio 的段，音频自动上传作音色+口型参考）
- 产物 gen/<id>.mp4；清单 gen/manifest.json（assemble.py 的输入）；提交记录 gen/tasks.json
- 断点续跑：manifest 里已有且文件存在的段自动跳过；单段失败只重跑那一段（--only）
- 报错出现 AigcComplianceConfirmationRequired = 该模型需要先去即梦网页端用一次完成首次确认
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
        sys.exit("找不到 dreamina CLI：先按 references/install.md 安装并 dreamina login")
    return exe

def run(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(r.stdout), r
    except json.JSONDecodeError:
        return None, r

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                        "-show_entries", "stream=width,height", "-show_entries", "format=duration",
                        "-of", "json", str(path)], capture_output=True, text=True)
    d = json.loads(r.stdout)
    w = d["streams"][0]["width"]; h = d["streams"][0]["height"]
    return w, h, float(d["format"]["duration"])

def submit(D, seg):
    base = [D, seg["command"],
            "--prompt", seg["prompt"],
            "--duration", str(seg["duration"]),
            "--video_resolution", seg["resolution"],
            "--model_version", seg["model"],
            "--poll", "0"]
    if seg["command"] == "image2video":
        base += ["--image", seg["reference_image"]]     # 比例由首帧图自动推断
    else:
        base += ["--image", seg["reference_image"]]
        if seg.get("ratio"):                            # multimodal2video 默认 16:9，必须显式给
            base += ["--ratio", seg["ratio"]]
        if seg.get("audio"):
            base += ["--audio", seg["audio"]]
    out, r = run(base)
    if out is None:
        msg = (r.stdout or "") + (r.stderr or "")
        sys.exit(f"提交失败（非 JSON 返回）：{msg.strip()[-500:]}")
    if out.get("gen_status") not in ("querying", "success"):
        msg = json.dumps(out, ensure_ascii=False)
        if "AigcComplianceConfirmationRequired" in msg:
            sys.exit(f"{seg['id']}：该模型（{seg['model']}）需要先在即梦网页端用一次完成首次确认，再到网页或这里重试。")
        sys.exit(f"{seg['id']} 提交失败：{msg[-500:]}")
    return out

def query(D, submit_id, download_dir=None):
    cmd = [D, "query_result", f"--submit_id={submit_id}"]
    if download_dir:
        cmd += [f"--download_dir={download_dir}"]
    out, r = run(cmd, timeout=600)
    return out or {"gen_status": "unknown", "raw": ((r.stdout or "") + (r.stderr or ""))[-300:]}

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    segs = plan["segments"]
    only = arg("--only")
    only = set(only.split(",")) if only else None
    timeout_s = int(arg("--timeout", "1800"))
    poll_s = int(arg("--poll", "20"))
    D = dreamina()

    gen = Path("gen"); gen.mkdir(exist_ok=True)
    manifest_path = gen / "manifest.json"; tasks_path = gen / "tasks.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    tasks = json.loads(tasks_path.read_text(encoding="utf-8")) if tasks_path.exists() else {}

    todo = [s for s in segs if (not only or s["id"] in only)]
    todo = [s for s in todo if not (manifest.get(s["id"], {}).get("file") and Path(manifest[s["id"]]["file"]).exists())]

    est = sum((s.get("est_credit") or 0) for s in todo)
    unknown = [s["id"] for s in todo if s.get("est_credit") is None]
    print(f"将提交 {len(todo)} 段：{'、'.join(s['id'] + '(' + s['model'] + ' ' + str(s['duration']) + 's)' for s in todo)}")
    print(f"预估 {est:g} 即梦积分" + (f"（{','.join(unknown)} 单价未实测，以提交返回 credit_count 为准）" if unknown else ""))
    if not has("--yes"):
        print("干跑结束。确认无误后加 --yes 真正提交。")
        return
    if not todo:
        print("没有需要生成的段（都已在 manifest）。")
        return

    # 1. 提交
    resub = has("--resubmit")   # 显式重拍：忽略旧 submit_id（配合 --only 用，旧任务积分不退）
    for s in todo:
        if not resub and s["id"] in tasks and tasks[s["id"]].get("submit_id") and not manifest.get(s["id"]):
            print(f"{s['id']} 复用已有 submit_id {tasks[s['id']]['submit_id']}")
            continue
        if resub:
            tasks.pop(s["id"], None)
        print(f"提交 {s['id']}（{s['model']} {s['duration']}s）…", flush=True)
        out = submit(D, s)
        est_remaining = (out.get("queue_info") or {}).get("estimated_remaining_seconds")
        tasks[s["id"]] = {"submit_id": out["submit_id"], "model": s["model"], "duration": s["duration"],
                          "credits": out.get("credit_count"), "logid": out.get("logid"),
                          "est_remaining_s": est_remaining}
        tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  submit_id={out['submit_id']}  扣 {out.get('credit_count')} 积分"
              + (f"  预计等待 {int(est_remaining)//60} 分" if isinstance(est_remaining, (int, float)) else ""))
        if isinstance(est_remaining, (int, float)) and est_remaining > 3600:
            print(f"  ⚠ {s['id']} 队列预估 {int(est_remaining)//3600} 小时：当前模型队列很挤，考虑换 seedance2.0mini（persona 默认）")
        time.sleep(3)   # 提交限速保护

    # 2. 轮询 + 下载
    pending = {s["id"]: tasks[s["id"]]["submit_id"] for s in todo
               if s["id"] in tasks and not (manifest.get(s["id"], {}).get("file") and Path(manifest[s["id"]]["file"]).exists())}
    deadline = {k: time.time() + timeout_s for k in pending}
    while pending:
        time.sleep(poll_s)
        for sid, sub in list(pending.items()):
            out = query(D, sub)
            st = out.get("gen_status")
            if st == "success":
                res = (out.get("result_json") or {}).get("videos") or []
                if not res:
                    print(f"{sid}: success 但没有视频产物：{json.dumps(out, ensure_ascii=False)[-300:]}")
                    del pending[sid]; continue
                downloaded = Path(res[0]["path"]) if res[0].get("path") and Path(res[0]["path"]).exists() else None
                if downloaded is None:
                    q = query(D, sub, download_dir=str(gen))
                    res = (q.get("result_json") or {}).get("videos") or []
                    downloaded = Path(res[0]["path"]) if res and res[0].get("path") and Path(res[0]["path"]).exists() else None
                if downloaded is None:
                    print(f"{sid}: 下载失败，下轮重试"); continue
                final = gen / f"{sid}.mp4"
                shutil.move(str(downloaded), final)
                w, h, dur = probe(final)
                manifest[sid] = {"submit_id": sub, "file": str(final), "w": w, "h": h,
                                 "duration": round(dur, 3), "model": tasks[sid]["model"],
                                 "credits": tasks[sid].get("credits")}
                manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  ✓ {sid} → {final}（{w}×{h} {dur:.1f}s）")
                del pending[sid]
            elif st == "fail":
                reason = out.get("fail_reason") or json.dumps(out, ensure_ascii=False)[-300:]
                print(f"  ✗ {sid} 生成失败：{reason}（用 --only {sid} 重拍）")
                del pending[sid]
            else:
                if time.time() > deadline[sid]:
                    print(f"  ⏱ {sid} 等待超过 {timeout_s}s 仍是 {st}，submit_id={sub} 已存 gen/tasks.json，稍后重跑本脚本可续。")
                    del pending[sid]
                else:
                    print(f"  … {sid} {st}")
                    continue
    done = [s["id"] for s in todo if manifest.get(s["id"], {}).get("file")]
    print(f"完成 {len(done)}/{len(todo)} 段。下一步：python3 scripts/assemble.py <script.json> gen/manifest.json")

if __name__ == "__main__":
    main()
