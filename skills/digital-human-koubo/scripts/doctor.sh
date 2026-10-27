#!/bin/bash
# 本机环境检查：有的打 ✓ 跳过，缺的才列装法（先列本机系统的，再列其他方式）。不自动安装。
# 用法：bash doctor.sh        退出码 0 = 齐了，1 = 有缺的
OS=$(uname -s); case "$OS" in Darwin) SYS=mac;; Linux) SYS=linux;; MINGW*|MSYS*|CYGWIN*) SYS=win;; *) SYS=other;; esac
MISS=0; OPTMISS=0
ok(){ printf "  ✓ %s\n" "$1"; }
need(){ # need 名称 用途 mac装法 win装法 linux装法 其他装法
  MISS=1; printf "  ✗ %s（%s）\n" "$1" "$2"
  case $SYS in mac) first="$3";; win) first="$4";; linux) first="$5";; *) first="$6";; esac
  printf "      推荐：%s\n" "$first"
  for kv in "macOS|$3" "Windows|$4" "Linux|$5" "其他|$6"; do n=${kv%%|*}; v=${kv#*|}; [ "$v" = "$first" ] || [ -z "$v" ] || printf "      %s：%s\n" "$n" "$v"; done
}
optmiss(){ OPTMISS=1; printf "  ○ %s（可选）\n" "$1"; printf "      %s\n" "$2"; }
echo "数字人口播（即梦版）· 本机环境检查（$OS）"
command -v ffmpeg >/dev/null && ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" || need "ffmpeg" "抽帧、拼接、响度" "brew install ffmpeg" "winget install Gyan.FFmpeg  或  choco install ffmpeg" "sudo apt install ffmpeg  （或 dnf / pacman）" "ffmpeg.org 下载安装包"
PY=$(command -v python3.14 || command -v python3 || command -v python)
if [ -n "$PY" ]; then
  ok "Python $($PY -c 'import sys;print(sys.version.split()[0])')"
  for m in numpy:numpy PIL:pillow; do mod=${m%%:*}; pkg=${m#*:}
    $PY -c "import $mod" 2>/dev/null && ok "$pkg" || need "$pkg" "声音统一 / 预览图" "$PY -m pip install $pkg" "$PY -m pip install $pkg" "$PY -m pip install $pkg" "conda install $pkg"
  done
else need "Python 3" "计划、生成、质检、对齐脚本" "brew install python" "winget install Python.Python.3.12" "sudo apt install python3 python3-pip" "python.org 下载，或装 Anaconda / Miniconda"; fi
if command -v node >/dev/null; then
  v=$(node -v | tr -d v | cut -d. -f1); [ "$v" -ge 18 ] && ok "Node $(node -v)" || need "Node 18 以上（现在是 $(node -v)）" "Remotion 剪辑" "brew upgrade node" "winget upgrade OpenJS.NodeJS.LTS" "nvm install --lts" "nodejs.org 下载 LTS"
else need "Node 18+" "Remotion 剪辑" "brew install node" "winget install OpenJS.NodeJS.LTS" "sudo apt install nodejs npm  或  nvm install --lts" "nodejs.org 下载 LTS"; fi

echo "—— 生成通道 ——"
DM=$(command -v dreamina || [ -x "$HOME/bin/dreamina.exe" ] && echo "$HOME/bin/dreamina.exe" || [ -x "$HOME/bin/dreamina" ] && echo "$HOME/bin/dreamina" || command -v dreamina)
if [ -n "$DM" ] && command -v "$DM" >/dev/null 2>&1 || [ -x "$DM" ]; then
  ok "dreamina CLI（$DM）"
  CRED=$("$DM" user_credit 2>/dev/null | grep -o '"total_credit": [0-9.]*' | grep -o '[0-9.]*')
  if [ -n "$CRED" ]; then ok "即梦已登录，余额 $CRED 积分"; else need "即梦登录态" "生成数字人口播" "终端跑：dreamina login（浏览器授权）" "同左" "同左" "headless：dreamina login --headless 后 dreamina login checklogin"; fi
else need "dreamina CLI（即梦官方）" "数字人口播生成主力" "curl -s https://jimeng.jianying.com/cli | bash" "同左（Git Bash / WSL）" "同左" "装完跑 dreamina login 完成浏览器授权"; fi
if command -v apiz >/dev/null; then
  B=$(apiz account balance 2>/dev/null | grep -o '"balance": [0-9.]*' | grep -o '[0-9.]*$')
  ok "apiz CLI（余额 ${B:-?} 积分）"
else need "apiz CLI" "台词核验（align QC）/ TTS / 克隆声 / 备用生成" "curl -fsSL https://data.apiz.ai/cli/install.sh | bash  或见 apiz.ai 文档" "同左" "同左" "装完跑 apiz auth login 存 key"; fi

echo "—— 可选项 ——"
$PY -c "import edge_tts" 2>/dev/null && ok "edge-tts（旁白/指定音色）" || optmiss "edge-tts" "只有旁白段或指定音色才需要：$PY -m pip install edge-tts"
command -v whisper-cli >/dev/null && ok "whisper-cli（零积分回听）" || optmiss "whisper-cli" "默认 QC 走 apiz align（10 积分/段）；想零积分回听再装：brew install whisper-cpp / whisper.cpp Releases"
command -v jimeng >/dev/null && printf "  - npm jimeng-cli 已被官方 dreamina CLI 取代，可 npm uninstall -g jimeng-cli\n"

echo
if [ $MISS = 0 ]; then echo "必需项齐了。${OPTMISS:+有可选项没装（○），用到再装。}"; else echo "装好上面 ✗ 的项（任选一种方式），再跑一次 bash doctor.sh 确认。"; fi
exit $MISS
