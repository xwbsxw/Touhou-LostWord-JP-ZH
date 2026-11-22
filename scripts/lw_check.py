"""启动游戏并检测是否能存活（不需要屏幕解锁）。

用法: python lw_check.py [等待秒数]
输出: 进程是否存在、前台 Activity、是否出现崩溃/异常日志
"""
import subprocess, sys, time, re

ADB = r'tools\platform-tools\adb.exe'
PKG = 'jp.goodsmile.touhoulostword_android'
wait = int(sys.argv[1]) if len(sys.argv) > 1 else 90


def sh(cmd, root=False):
    if root:
        cmd = f"su -c '{cmd}'"
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True, text=True, errors='replace')
    return r.stdout


subprocess.run([ADB, 'shell', f"su -c 'am force-stop {PKG}'"], capture_output=True)
time.sleep(2)
subprocess.run([ADB, 'logcat', '-c'], capture_output=True)
subprocess.run([ADB, 'shell', "monkey -p %s -c android.intent.category.LAUNCHER 1" % PKG],
               capture_output=True)

alive_at = []
for i in range(0, wait, 10):
    time.sleep(10)
    pid = sh(f'pidof {PKG}', root=True).strip()
    alive_at.append((i + 10, pid or '-'))

pid = sh(f'pidof {PKG}', root=True).strip()
print('检查时间线:', alive_at)
print('最终 pid:', pid or '进程已退出')

act = sh('dumpsys activity activities | grep -m3 -E "ResumedActivity|topResumedActivity"')
print('前台:', act.strip()[:300])

log = subprocess.run([ADB, 'logcat', '-d', '-v', 'brief'], capture_output=True, text=True,
                     errors='replace').stdout
pat = re.compile(r'(FATAL EXCEPTION|AndroidRuntime.*FATAL|signal 1[01]|SIGSEGV|ANR in|Force finishing|'
                 r'Exception|Error: )', re.I)
lines = [l for l in log.splitlines() if pat.search(l)]
print(f'可疑日志 {len(lines)} 行:')
for l in lines[:25]:
    print('  ', l[:200])
