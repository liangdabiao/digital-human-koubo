# 从一张照片做一个新数字人

1. **照片**：一张正脸、光线均匀、头发不挡脸的人物照（数字人照片或自己的生活照都行）。从视频里取帧时挑嘴闭着的一帧。只用本人或明确同意的人的照片。放到 `assets/` 下（如 `assets/host_me.jpg`）。
2. **四视图**（要换角度拍摄时才做）：`dreamina text2image --prompt="同一个女生同一套衣服发型，四格并排——正面/左侧/右侧/背面，浅灰无缝背景，不出现任何文字" --ratio=16:9 --resolution_type=2k`；或用 `dreamina image edit` 在原照基础上改。费用以提交返回为准，先报价再做。
3. **多版本对比**：同一句 6 秒台词各拍一版，`generate_segments.py plan.json --yes --only s1` 分别换参考图跑，并排看：脸像不像、口型对不对、动作自不自然、声音喜不喜欢。
4. **选定**：把参考图路径写进 persona.json（`media.reference_image` 或 `other_hosts.<名字>.reference_image`），补 `look` 和 `voice_desc`。
5. **先拍一段**：`build_plan.py` + `generate_segments.py --only 第1段` 确认形象和音色，用户满意再批量。
6. 换音色（克隆声/指定音色）见 references/voice.md。
