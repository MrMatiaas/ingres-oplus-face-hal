#!/usr/bin/env bash
# Builds patched services.jar + SystemUI.apk for the OPlusFace bridge on ColorOS 17.
# Needs: apktool 3.x, python3, java. Inputs in ./in : services.jar, SystemUI.apk,
# bridge.dex (classes.dex from ryanistr/OPlusFace AUTOPATCH/faceunlock).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
IN=${IN:-$PWD/in}; OUT=${OUT:-$PWD/out}; W=$(mktemp -d)
mkdir -p "$OUT"
FACE=com/android/server/biometrics/sensors/face

# --- services.jar ---
apktool d -r -f -o "$W/sj" "$IN/services.jar"
python3 -I "$HERE/patch_services_smali.py" "$W/sj/smali"
# classes.dex is at the 64K method-ref limit: move patched classes to a new dex
N=$(ls -d "$W"/sj/smali_classes* | wc -l); NEW="$W/sj/smali_classes$((N + 2))"
mkdir -p "$NEW/$FACE/aidl"
mv "$W/sj/smali/$FACE/FaceService.smali" "$W/sj/smali/$FACE/FaceService\$FaceServiceWrapper.smali" "$NEW/$FACE/"
mv "$W/sj/smali/$FACE/aidl/FaceProvider.smali" "$NEW/$FACE/aidl/"
apktool b -o "$W/sj_built.jar" "$W/sj"
python3 -I "$HERE/repack_jar.py" "$IN/services.jar" "$W/sj_built.jar" "$OUT/services.jar" "$IN/bridge.dex"

# --- SystemUI.apk ---
apktool d -r -f --no-res -o "$W/sui" "$IN/SystemUI.apk" 2>/dev/null || apktool d -r -f -o "$W/sui" "$IN/SystemUI.apk"
mkdir -p "$W/ap"; cp "$W/sj/apktool.yml" "$W/ap/"
sed -i 's/^apkFileName:.*/apkFileName: dummy.jar/' "$W/ap/apktool.yml"
mv "$W/sui/smali" "$W/ap/smali"
python3 -I "$HERE/patch_systemui_smali.py" "$W/ap/smali" "$W/ap/smali_classes2"
apktool b -o "$W/ap_built.jar" "$W/ap"
unzip -q -o "$W/ap_built.jar" classes.dex classes2.dex -d "$W/apx"
LAST=$(unzip -l "$IN/SystemUI.apk" | grep -oE 'classes[0-9]*\.dex' | sed 's/classes\([0-9]*\)\.dex/\1/' | sort -n | tail -1)
python3 -I "$HERE/apk_replace_dex_keep_sig.py" "$IN/SystemUI.apk" "$OUT/SystemUI.apk" \
    classes.dex="$W/apx/classes.dex" "classes$((LAST + 1)).dex=$W/apx/classes2.dex"
rm -rf "$W"
echo "Done. Remove oat/arm64/services.* and SystemUI oat/ from the ROM tree."
