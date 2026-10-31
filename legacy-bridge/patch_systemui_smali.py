#!/usr/bin/env python3
"""SystemUI: AuthController.isFaceAuthEnrolled(I)Z reads persist.sys.oplus.isFaceEnrolled
(set by the bridge) instead of the cache that is only refreshed by HAL events.
Moves AuthController.smali to <new_dir> so it can be assembled into its own dex.
Usage: patch_systemui_smali.py <smali dir of classes.dex> <new_dir>
"""
import os, re, shutil, sys

src_dir, new_dir = sys.argv[1:3]
rel = 'com/android/systemui/biometrics/AuthController.smali'
os.makedirs(os.path.dirname(os.path.join(new_dir, rel)), exist_ok=True)
dst = os.path.join(new_dir, rel)
shutil.move(os.path.join(src_dir, rel), dst)
h = '.method public final isFaceAuthEnrolled(I)Z'
body = '''    .registers 4
    const-string v0, "persist.sys.oplus.isFaceEnrolled"
    const/4 v1, 0x0
    invoke-static {v0, v1}, Landroid/os/SystemProperties;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    return v0
'''
s = open(dst).read()
s, n = re.subn(r'^' + re.escape(h) + r'\n.*?^\.end method\n', h + '\n' + body + '.end method\n', s, flags=re.M | re.S)
assert n == 1, n
open(dst, 'w').write(s)
print('patched', dst)
