# ingres-oplus-face-hal

Face unlock for ColorOS 17 (OnePlus 15 / Android 17) ported to non-Oplus devices,
developed on a Poco F4 GT (`ingres`, SM8450) running an OxygenOS/ColorOS 17 port
on top of the HyperOS vendor.

> Work in progress. Full guides in Spanish and English will be added once the
> real HAL is finished.

## Status

| Part | State |
|---|---|
| `legacy-bridge/` — OPlusFace bridge in `system_server`, adapted to CO17 | Works (enroll + keyguard unlock) |
| `hal/` — real `android.hardware.biometrics.face.IFace` HAL + Oplus extension | In progress |

## legacy-bridge

Port of [ryanistr/OPlusFace](https://github.com/ryanistr/OPlusFace) (Motorola /
Megvii face engine running inside `system_server`) to ColorOS 17. The original
patches do not apply on CO17; this version:

- `FaceService.getDeclaredInstances()` → `["default"]`.
- `FaceServiceWrapper.registerAuthenticators()` no longer bails out without HAL
  configs; `getProviders()` builds a `default` provider with fake `SensorProps`.
- `FaceProvider` auth/enroll/remove/challenge methods go to `FaceAuthBridge`.
- Both `FaceProvider.scheduleForSensor()` overloads become no-ops. Without this,
  `FaceStartUserClient` retries forever without a HAL (≈80 % CPU in system_server).
- Patched classes are moved to a new dex: CO17's `classes.dex` is at the 64K
  method-reference limit.
- SystemUI `AuthController.isFaceAuthEnrolled()` reads
  `persist.sys.oplus.isFaceEnrolled`, so the keyguard picks up a new enrollment
  without restarting SystemUI. The APK is rebuilt keeping its v2 signing block.

### Build

```sh
mkdir in
cp /path/to/services.jar /path/to/SystemUI.apk in/
cp OPlusFace/AUTOPATCH/faceunlock/classes.dex in/bridge.dex
legacy-bridge/build.sh          # needs apktool 3.x, python3, java
```

Then in the ROM tree: replace both files, delete `framework/oat/arm64/services.*`
and `priv-app/SystemUI/oat/`, and add the Megvii libraries
(`libmegface.so`, `libFaceDetectCA.so`, `libMegviiUnlock.so`,
`libMegviiUnlock-jni-1.2.so` in `system/lib64`), the models
(`system/etc/face/model_file`, `panorama_mgb`) and `init.universal-face.rc`.

**The Megvii/Motorola binaries are proprietary and are not distributed here.**
They used to be in the OPlusFace repository history (`Compiled/` folder).

## Oplus face extension protocol (CO17)

`FaceServiceExtImpl` (`IOplusFaceManager`) is attached through
`FaceService$OplusFaceServiceWrapper.setExtensionWrapper()`. It talks to the HAL
with extra transaction codes on the standard AIDL binders:

| Direction | Binder | Code | Payload |
|---|---|---|---|
| framework → HAL | `IFace/default` | `1001` | `int switchType, boolean on` → `int` |
| framework → HAL | `IFace/default` | `1002` | `int cmdId, int len, byte[] buf` → `int` |
| framework → HAL | `IFace/default` | `1005` | `int, int` (dynamic log) |
| HAL → framework | `ISessionCallback` | any non-AIDL code | `int cmdId, int len, byte[] buf` → `FaceProvider.handleOnFaceCmd` |

## Credits

- [ryanistr/OPlusFace](https://github.com/ryanistr/OPlusFace), Danda420, LazyBones
- [null-dev/UniversalAuth](https://github.com/null-dev/UniversalAuth)
