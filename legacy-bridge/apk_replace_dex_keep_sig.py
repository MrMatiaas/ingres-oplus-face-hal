#!/usr/bin/env python3
"""Replaces/adds dex files in an APK WITHOUT touching the rest of the file and
keeping the original APK Signing Block (v2/v3). New local entries are appended
after the last original entry; the central directory is rewritten to point at
them (the old entries stay as unreferenced bytes). Only valid for preinstalled
system apps, whose signatures are collected without verification.
Usage: apk_replace_dex_keep_sig.py <in.apk> <out.apk> name=path.dex [name=path.dex ...]
"""
import struct, sys, zlib

src = open(sys.argv[1], 'rb').read()
repl = dict(a.split('=', 1) for a in sys.argv[3:])
e = src.rfind(b'PK\x05\x06')
n, cd_size, cd_off = struct.unpack_from('<HII', src, e + 10)
assert src[cd_off - 16:cd_off] == b'APK Sig Block 42', 'no v2 signing block'
sb_size = struct.unpack_from('<Q', src, cd_off - 24)[0]
sb_start = cd_off - sb_size - 8
entries, p = [], cd_off
for _ in range(n):
    fnl, exl, cml = struct.unpack_from('<HHH', src, p + 28)
    entries.append((src[p + 46:p + 46 + fnl].decode(), src[p:p + 46 + fnl + exl + cml]))
    p += 46 + fnl + exl + cml
out = bytearray(src[:sb_start])
new_cd = {}
for name, path in repl.items():
    data, nb = open(path, 'rb').read(), name.encode()
    pad = (-(len(out) + 30 + len(nb))) % 4
    crc, off = zlib.crc32(data) & 0xffffffff, len(out)
    out += struct.pack('<IHHHHHIIIHH', 0x04034b50, 10, 0, 0, 0, 0x21, crc, len(data), len(data), len(nb), pad) + nb + b'\0' * pad + data
    new_cd[name] = struct.pack('<IHHHHHHIIIHHHHHII', 0x02014b50, 0x0314, 10, 0, 0, 0, 0x21, crc, len(data), len(data),
                               len(nb), 0, 0, 0, 0, 0o100644 << 16, off) + nb
cd = bytearray()
for name, raw in entries:
    cd += new_cd.pop(name, raw)
for raw in new_cd.values():
    cd += raw
cd_new_off = len(out) + (cd_off - sb_start)
out += src[sb_start:cd_off] + cd
eocd = bytearray(src[e:])
total = n + sum(1 for k in repl if k not in dict(entries))
struct.pack_into('<HHII', eocd, 8, total, total, len(cd), cd_new_off)
open(sys.argv[2], 'wb').write(out + eocd)
print('written', sys.argv[2])
