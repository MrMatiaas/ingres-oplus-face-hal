#!/usr/bin/env python3
"""Rebuilds services.jar: keeps every non-dex entry of the original jar, takes the
dex files rebuilt by apktool and appends extra dex files (e.g. the bridge dex).
Stored entries are 4-byte aligned (zipalign equivalent).
Usage: repack_jar.py <original.jar> <apktool_built.jar> <out.jar> [extra.dex ...]
"""
import sys, zipfile

orig, built, out_path, *extra = sys.argv[1:]
src, bld = zipfile.ZipFile(orig), zipfile.ZipFile(built)
dexes = sorted((n for n in bld.namelist() if n.startswith('classes') and n.endswith('.dex')),
               key=lambda n: (len(n), n))
items = [(i, src.read(i.filename)) for i in src.infolist()
         if not (i.filename.startswith('classes') and i.filename.endswith('.dex'))]
items += [(n, bld.read(n)) for n in dexes]
for k, path in enumerate(extra, start=len(dexes) + 1):
    items.append((f'classes{k}.dex', open(path, 'rb').read()))

with open(out_path, 'wb') as f:
    z = zipfile.ZipFile(f, 'w')
    for info, data in items:
        if isinstance(info, str):
            zi = zipfile.ZipInfo(info, date_time=(2009, 1, 1, 0, 0, 0))
            zi.compress_type, zi.external_attr = zipfile.ZIP_STORED, 0o644 << 16
        else:
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type, zi.external_attr = info.compress_type, info.external_attr
        if zi.compress_type == zipfile.ZIP_STORED:
            zi.extra = b'\0' * ((-(f.tell() + 30 + len(zi.filename.encode()))) % 4)
        z.writestr(zi, data)
    z.close()
print('written', out_path, [n for n in zipfile.ZipFile(out_path).namelist() if n.endswith('.dex')])
