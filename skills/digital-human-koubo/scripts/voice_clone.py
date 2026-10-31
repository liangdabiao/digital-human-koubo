#!/usr/bin/env python3
"""海螺声音克隆（apiz minimax/voice-clone）：上传音频样本 → 克隆音色 → 试听验证。

用法：
  python3 voice_clone.py <样本音频.mp3|m4a|wav> [--name 我的音色] [--test-text "试听句子"]

样本要求：mp3/m4a/wav，10 秒–5 分钟，≤20MB（安静环境、离麦 20 厘米、无混响）。
流程：
  1. apiz upload 样本 → 公网 URL
  2. apiz generate --model minimax/voice-clone（自定义 voice_id = --name）
  3. apiz voices list 确认出现在 user_voices
  4. apiz speak 用新音色合成试听句 → clone_test.mp3（人耳确认像不像）
产出：打印 voice_id。把它填进：
  - digital-human-koubo/persona.json → voice.tts.cloned_voice_id
  - tts.py 的 --voice 参数 / narrate_edge.py 的 --voice
之后走 multimodal2video 音频驱动（tts.py 合成 → 音频作参考）或纯旁白。
红线：只克隆用户本人或明确授权者的声音。
"""
import json, shutil, subprocess, sys, urllib.request
from pathlib import Path

def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sample = Path(sys.argv[1])
    if not sample.exists():
        sys.exit(f"样本不存在：{sample}")
    size = sample.stat().st_size
    if size > 20 * 1024 * 1024:
        sys.exit(f"样本 {size/1e6:.1f}MB 超 20MB 上限：先剪切/压缩")
    apiz = shutil.which("apiz")
    name = arg("--name", "my-voice")
    test_text = arg("--test-text", "大家好，这是我的声音克隆试听，很高兴认识你。")

    r = subprocess.run([apiz, "upload", str(sample)], capture_output=True, text=True)
    url = json.loads(r.stdout)["public_url"]
    print(f"样本已上传：{url}")

    params = json.dumps({"voice_id": name, "file_url": url}, ensure_ascii=False)
    r = subprocess.run([apiz, "generate", "tts", "--model", "minimax/voice-clone",
                        "--params", params, "--wait", "--wait-timeout", "10m", "--json"],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"克隆提交失败：{(r.stdout or r.stderr)[-400:]}")
    if d.get("status") != "completed":
        # 400 会提示参数名，照改（如 file_id/file_url/base64）；复现报错原文给下一步
        sys.exit(f"克隆失败：{json.dumps(d, ensure_ascii=False)[-400:] if d.get('status') else (r.stdout or r.stderr)[-400:]}")
    print("克隆任务完成：", json.dumps(d.get("result", {}), ensure_ascii=False)[:300])

    r = subprocess.run([apiz, "voices", "list", "--json"], capture_output=True, text=True)
    vs = json.loads(r.stdout).get("user_voices", [])
    hit = [v for v in vs if name in (v.get("voice_id", "") + v.get("voice_name", ""))]
    if not hit:
        print("⚠ user_voices 里没找到，克隆可能异步生效中——几分钟后重跑 apiz voices list 确认")
    else:
        print("user_voices 命中：", json.dumps(hit[0], ensure_ascii=False))
    vid = hit[0]["voice_id"] if hit else name

    r = subprocess.run([apiz, "speak", test_text, "--voice", vid,
                        "--output-file", "clone_test.mp3"], capture_output=True, text=True)
    if Path("clone_test.mp3").exists():
        print(f"试听已生成：clone_test.mp3（voice_id={vid}）——人耳确认像不像，像就把 voice_id 填进 persona.json → voice.tts.cloned_voice_id")
    else:
        print(f"⚠ 试听合成失败：{(r.stdout + r.stderr)[-300:]}（voice_id={vid} 仍可能有效）")

if __name__ == "__main__":
    main()
