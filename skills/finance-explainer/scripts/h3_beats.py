#!/usr/bin/env python3
"""逐拍用 apiz MiniMax-H3 生成出镜片段（人物真实感优先的默认通道）。
用法：python3 h3_beats.py <episode.json> <anchor图> <gen目录> [--resolution 480p] [--only c01,c05] [--lead "定妆描述"]
读拍表里 host != off 的拍，H3 生成原生配音口播 → gen/h3_<id>.mp4，更新 gen/clips.json。
之后照常跑 sync_beats.py（原生音轨 + apiz align 打轴）→ build_timeline → 渲染。
H3 参数结构（实测）：params.content = [{type:text},{type:image_url,image_url:{url},role:first_frame}]；duration 4-15 整数；480p 12/秒 + context 7/次。
"""
import json, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d

PROMPT = ("固定机位中景，{lead}，不推拉。画面中的女主播正对镜头，像亲切的财经解说博主一样看镜头讲话，"
          "嘴部始终清晰可见：眼神明亮专注，自然眨眼，讲到关键词时偶尔挑眉、微笑、小幅点头，双手做解释性手势。"
          "她用普通话清晰地说：\"{line}\" 语气亲切自然，语速适中。"
          "真实摄影质感，皮肤纹理真实自然，人物长相、发型、服装与参考图完全一致。"
          "音频：只有她清晰的说话声和安静的房间底噪，没有音乐。画面无字幕无文字无水印。")

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def upload(apiz, path):
    r = sh([apiz, "upload", str(path)])
    return json.loads(r.stdout)["public_url"]

def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    ep = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    anchor = Path(sys.argv[2]); gen = Path(sys.argv[3])
    gen.mkdir(exist_ok=True)
    apiz = shutil.which("apiz")
    only = arg("--only")
    only = set(only.split(",")) if only else None
    lead = arg("--lead", "书房背景，暖光台灯，坐在书桌前")
    res = arg("--resolution", "480p")

    beats = [b for b in ep["beats"] if b.get("narration") and b.get("host") != "off"
             and (not only or b["id"] in only)]
    clips_p = gen / "clips.json"
    clips = json.loads(clips_p.read_text(encoding="utf-8")) if clips_p.exists() else {}
    print(f"H3 生成 {len(beats)} 拍（{res}）：{'、'.join(b['id'] for b in beats)}")
    for b in beats:
        bid = b["id"]
        if clips.get(bid) and Path(clips[bid]).exists() and not arg("--resubmit"):
            print(f"{bid} 已有片段，跳过"); continue
        # 时长：按台词字数估（4-15 整数），宁长勿短，后面 sync_beats 会裁
        n = len([c for c in b["narration"] if c not in "，。！？；：、,.!?;: "])
        dur = max(4, min(15, int(n / 4.4) + 2))
        prompt = PROMPT.format(lead=lead, line=b["narration"])
        aurl = upload(apiz, anchor)
        params = json.dumps({
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": aurl}, "role": "first_frame"},
            ],
            "duration": dur, "resolution": res,
        }, ensure_ascii=False)
        print(f"提交 {bid}（H3 {res} ~{dur}s）…", flush=True)
        r = sh([apiz, "generate", "tts", "--model", "minimax/h3", "--params", params,
                "--wait", "--wait-timeout", "15m", "--json"])
        out_p = gen / f"h3_{bid}.result.json"
        out_p.write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
        try:
            d = json.loads(r.stdout)
        except json.JSONDecodeError:
            sys.exit(f"{bid} 提交失败：{(r.stdout or r.stderr)[-400:]}")
        if d.get("status") != "completed":
            sys.exit(f"{bid} 失败：{json.dumps(d, ensure_ascii=False)[-400:]}")
        vurl = d["result"]["video_url"]
        price = d.get("price")
        dst = gen / f"h3_{bid}.mp4"
        urllib.request.urlretrieve(vurl, dst)
        clips[bid] = str(dst)
        clips_p.write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  ✓ {bid} → {dst}（{price} 积分）")
        time.sleep(2)
    print("完成。下一步：python3 ../skills/finance-explainer/scripts/sync_beats.py episode.json voice gen --public engine/public")

if __name__ == "__main__":
    main()
