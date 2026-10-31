# Guide: ColorOS 17 face unlock with MT Manager

[Versión en español](GUIA_MT_MANAGER.md)

Manual version of `legacy-bridge/` (Megvii/Motorola face engine from
[OPlusFace](https://github.com/ryanistr/OPlusFace) running inside `system_server`),
adapted to ColorOS 17 / Android 17. Tested on Poco F4 GT (`ingres`).

> **Two warnings first**
>
> 1. **64K limit in `services.jar`.** CO17's `classes.dex` sits right at the 65,536
>    method-reference limit and the patches exceed it by ~10. `build.sh` handles this
>    by moving the 3 patched classes to a new dex. If MT Manager fails with
>    *too many method references* / 65536 when compiling, use
>    `legacy-bridge/build.sh` on a PC.
> 2. **The SystemUI patch is optional and risky with MT.** The APK is v2-signed only;
>    if saving drops the signing block, SystemUI will not load (black screen).
>    Everything works without it: just **reboot once after enrolling a face**.

## 0. Requirements
- Root and MT Manager with **Dex Editor Plus**.
- Backup of `services.jar` and `system/framework/oat/arm64/services.*`.
- From the OPlusFace history (`Compiled/` folder, commit before `10be794`). They are proprietary and not distributed here:
  - bridge `classes.dex` (same as `AUTOPATCH/faceunlock/classes.dex`)
  - `libmegface.so`, `libFaceDetectCA.so`, `libMegviiUnlock.so`, `libMegviiUnlock-jni-1.2.so`
  - `model_file`, `panorama_mgb`, `init.universal-face.rc`

Paths: in a DNA tree, `.../system/system/...`; on a mounted system, `/system/...`.

## 1. Copy files

| File | Destination | Mode |
|---|---|---|
| the 4 `.so` | `system/lib64/` | 644 |
| `model_file`, `panorama_mgb` | `system/etc/face/` (create, 755) | 644 |
| `init.universal-face.rc` | `system/etc/init/` | 644 |

If you build with DNA, append to `config/system_fs_config`:

```
system/system/etc/face 0 0 0755
system/system/etc/face/model_file 0 0 0644
system/system/etc/face/panorama_mgb 0 0 0644
system/system/etc/init/init.universal-face.rc 0 0 0644
system/system/lib64/libmegface.so 0 0 0644
system/system/lib64/libFaceDetectCA.so 0 0 0644
system/system/lib64/libMegviiUnlock.so 0 0 0644
system/system/lib64/libMegviiUnlock-jni-1.2.so 0 0 0644
```

and to `config/system_file_contexts`:

```
/system/system/etc/face u:object_r:system_file:s0
/system/system/etc/face/model_file u:object_r:system_file:s0
/system/system/etc/face/panorama_mgb u:object_r:system_file:s0
/system/system/etc/init/init\.universal-face\.rc u:object_r:system_file:s0
/system/system/lib64/libmegface\.so u:object_r:system_lib_file:s0
/system/system/lib64/libFaceDetectCA\.so u:object_r:system_lib_file:s0
/system/system/lib64/libMegviiUnlock\.so u:object_r:system_lib_file:s0
/system/system/lib64/libMegviiUnlock-jni-1\.2\.so u:object_r:system_lib_file:s0
```

## 2. Patch `services.jar`
Open `system/framework/services.jar` in MT → **Dex Editor Plus** → select **all**
`classes*.dex`. Replace **the whole method** (from `.method` to `.end method`) each time.

### 2.1 `com.android.server.biometrics.sensors.face.FaceService`

```smali
.method public static getDeclaredInstances()[Ljava/lang/String;
    .registers 3
    const/4 v0, 0x1
    new-array v0, v0, [Ljava/lang/String;
    const-string v1, "default"
    const/4 v2, 0x0
    aput-object v1, v0, v2
    return-object v0
.end method
```

### 2.2 `com.android.server.biometrics.sensors.face.FaceService$FaceServiceWrapper`
`registerAuthenticators` no longer bails out without a HAL and `getProviders`
builds the `default` sensor with fake `SensorProps`.

```smali
.method public registerAuthenticators(Landroid/hardware/face/FaceSensorConfigurations;)V
    .registers 4
    invoke-super {p0}, Landroid/hardware/face/IFaceService$Stub;->registerAuthenticators_enforcePermission()V
    iget-object v0, p0, Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper;->this$0:Lcom/android/server/biometrics/sensors/face/FaceService;
    invoke-static {v0}, Lcom/android/server/biometrics/sensors/face/FaceService;->-$$Nest$fgetmRegistry(Lcom/android/server/biometrics/sensors/face/FaceService;)Lcom/android/server/biometrics/sensors/face/FaceServiceRegistry;
    move-result-object v0
    new-instance v1, Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper$$ExternalSyntheticLambda0;
    invoke-direct {v1, p0, p1}, Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper$$ExternalSyntheticLambda0;-><init>(Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper;Landroid/hardware/face/FaceSensorConfigurations;)V
    invoke-virtual {v0, v1}, Lcom/android/server/biometrics/sensors/face/FaceServiceRegistry;->registerAll(Ljava/util/function/Supplier;)V
    return-void
.end method
```

```smali
.method private getProviders(Landroid/hardware/face/FaceSensorConfigurations;)Ljava/util/List;
    .registers 8
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Landroid/hardware/face/FaceSensorConfigurations;",
            ")",
            "Ljava/util/List<",
            "Lcom/android/server/biometrics/sensors/face/ServiceProvider;",
            ">;"
        }
    .end annotation
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V
    new-instance v1, Landroid/hardware/biometrics/face/SensorProps;
    invoke-direct {v1}, Landroid/hardware/biometrics/face/SensorProps;-><init>()V
    new-instance v2, Landroid/hardware/biometrics/common/CommonProps;
    invoke-direct {v2}, Landroid/hardware/biometrics/common/CommonProps;-><init>()V
    const/4 v3, 0x1
    iput v3, v2, Landroid/hardware/biometrics/common/CommonProps;->sensorId:I
    iput v3, v2, Landroid/hardware/biometrics/common/CommonProps;->maxEnrollmentsPerUser:I
    iput-object v2, v1, Landroid/hardware/biometrics/face/SensorProps;->commonProps:Landroid/hardware/biometrics/common/CommonProps;
    new-array v2, v3, [Landroid/hardware/biometrics/face/SensorProps;
    const/4 v3, 0x0
    aput-object v1, v2, v3
    new-instance v1, Landroid/util/Pair;
    const-string v4, "default"
    invoke-direct {v1, v4, v2}, Landroid/util/Pair;-><init>(Ljava/lang/Object;Ljava/lang/Object;)V
    iget-object v2, p0, Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper;->this$0:Lcom/android/server/biometrics/sensors/face/FaceService;
    invoke-static {v2}, Lcom/android/server/biometrics/sensors/face/FaceService;->-$$Nest$fgetmFaceProviderFunction(Lcom/android/server/biometrics/sensors/face/FaceService;)Lcom/android/server/biometrics/sensors/face/FaceService$FaceProviderFunction;
    move-result-object v2
    invoke-interface {v2, v1, v3}, Lcom/android/server/biometrics/sensors/face/FaceService$FaceProviderFunction;->getFaceProvider(Landroid/util/Pair;Z)Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;
    move-result-object v2
    invoke-interface {v0, v2}, Ljava/util/List;->add(Ljava/lang/Object;)Z
    return-object v0
.end method
```

### 2.3 `com.android.server.biometrics.sensors.face.aidl.FaceProvider`
14 methods; note there are two `scheduleAuthenticate` and two `scheduleForSensor`
with different signatures. **Both empty `scheduleForSensor` are mandatory**:
without them `FaceStartUserClient` retries forever and `system_server` sits at ~80 % CPU.

```smali
.method private initSensors(Z[Landroid/hardware/biometrics/face/SensorProps;)V
    .registers 12
    iget-object v0, p0, Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;->mContext:Landroid/content/Context;
    invoke-static {v0}, Lax/nd/faceunlock/FaceAuthBridge;->init(Landroid/content/Context;)V
    new-instance v0, Landroid/hardware/biometrics/face/SensorProps;
    invoke-direct {v0}, Landroid/hardware/biometrics/face/SensorProps;-><init>()V
    new-instance v1, Landroid/hardware/biometrics/common/CommonProps;
    invoke-direct {v1}, Landroid/hardware/biometrics/common/CommonProps;-><init>()V
    const/4 v2, 0x1
    iput v2, v1, Landroid/hardware/biometrics/common/CommonProps;->sensorId:I
    iput v2, v1, Landroid/hardware/biometrics/common/CommonProps;->maxEnrollmentsPerUser:I
    iput-object v1, v0, Landroid/hardware/biometrics/face/SensorProps;->commonProps:Landroid/hardware/biometrics/common/CommonProps;
    const/4 v1, 0x0
    invoke-direct {p0, v0, v1}, Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;->addAidlSensors(Landroid/hardware/biometrics/face/SensorProps;Z)V
    invoke-static {}, Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;->getExtImpl()Lcom/android/server/biometrics/sensors/face/aidl/IFaceProviderExt;
    move-result-object v2
    move-object v3, p0
    iget-object v4, p0, Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;->mContext:Landroid/content/Context;
    const/4 v1, 0x1
    new-array v5, v1, [Landroid/hardware/biometrics/face/SensorProps;
    const/4 v1, 0x0
    aput-object v0, v5, v1
    iget-object v6, p0, Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;->mHalInstanceName:Ljava/lang/String;
    iget-object v7, p0, Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;->mHandler:Landroid/os/Handler;
    invoke-interface/range {v2 .. v7}, Lcom/android/server/biometrics/sensors/face/aidl/IFaceProviderExt;->init(Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;Landroid/content/Context;[Landroid/hardware/biometrics/face/SensorProps;Ljava/lang/String;Landroid/os/Handler;)V
    return-void
.end method
```

```smali
.method public cancelAuthentication(ILandroid/os/IBinder;J)V
    .registers 8
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_end
    invoke-virtual {v0}, Lax/nd/faceunlock/FaceAuthBridge;->stopAuthenticate()V
    :cond_end
    return-void
.end method
```

```smali
.method public cancelEnrollment(ILandroid/os/IBinder;J)V
    .registers 8
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_end
    invoke-virtual {v0}, Lax/nd/faceunlock/FaceAuthBridge;->stopEnroll()V
    :cond_end
    return-void
.end method
```

```smali
.method public scheduleGenerateChallenge(IILandroid/os/IBinder;Landroid/hardware/face/IFaceServiceReceiver;Ljava/lang/String;)V
    .registers 9
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_end
    invoke-virtual {v0, p1, p2, p4}, Lax/nd/faceunlock/FaceAuthBridge;->generateChallenge(IILjava/lang/Object;)V
    :cond_end
    return-void
.end method
```

```smali
.method public scheduleRemove(ILandroid/os/IBinder;IILandroid/hardware/face/IFaceServiceReceiver;Ljava/lang/String;)V
    .registers 10
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_end
    invoke-virtual {v0, p4, p3, p5}, Lax/nd/faceunlock/FaceAuthBridge;->remove(IILjava/lang/Object;)V
    :cond_end
    return-void
.end method
```

```smali
.method public scheduleRevokeChallenge(IILandroid/os/IBinder;Ljava/lang/String;J)V
    .registers 10
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_end
    const/4 v2, 0x0
    invoke-virtual {v0, p1, p2, v2}, Lax/nd/faceunlock/FaceAuthBridge;->revokeChallenge(IILjava/lang/Object;)V
    :cond_end
    return-void
.end method
```

```smali
.method public getAuthenticatorId(II)J
    .registers 7
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual {v0}, Lax/nd/faceunlock/FaceAuthBridge;->getAuthenticatorId()J
    move-result-wide v0
    return-wide v0
    :cond_0
    const-wide/16 v0, 0x0
    return-wide v0
.end method
```

```smali
.method public getEnrolledFaces(II)Ljava/util/List;
    .registers 7
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(II)",
            "Ljava/util/List<",
            "Landroid/hardware/face/Face;",
            ">;"
        }
    .end annotation
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual {v0, p1, p2}, Lax/nd/faceunlock/FaceAuthBridge;->getEnrolledFaces(II)Ljava/util/List;
    move-result-object v0
    return-object v0
    :cond_0
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V
    return-object v0
.end method
```

```smali
.method public isHardwareDetected(I)Z
    .registers 3
    const/4 v0, 0x1
    return v0
.end method
```

```smali
.method public scheduleAuthenticate(Landroid/os/IBinder;JILcom/android/server/biometrics/sensors/ClientMonitorCallbackConverter;Landroid/hardware/face/FaceAuthenticateOptions;ZIZ)J
    .registers 20
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual/range {p6 .. p6}, Landroid/hardware/face/FaceAuthenticateOptions;->getUserId()I
    move-result v1
    invoke-virtual/range {p6 .. p6}, Landroid/hardware/face/FaceAuthenticateOptions;->getSensorId()I
    move-result v2
    move-object/from16 v3, p5
    invoke-virtual {v0, v2, v1, v3}, Lax/nd/faceunlock/FaceAuthBridge;->startAuthenticate(IILjava/lang/Object;)V
    :cond_0
    const-wide/16 v0, 0x1
    return-wide v0
.end method
```

```smali
.method public scheduleAuthenticate(Landroid/os/IBinder;JILcom/android/server/biometrics/sensors/ClientMonitorCallbackConverter;Landroid/hardware/face/FaceAuthenticateOptions;JZIZ)V
    .registers 22
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual/range {p6 .. p6}, Landroid/hardware/face/FaceAuthenticateOptions;->getUserId()I
    move-result v1
    invoke-virtual/range {p6 .. p6}, Landroid/hardware/face/FaceAuthenticateOptions;->getSensorId()I
    move-result v2
    move-object/from16 v3, p5
    invoke-virtual {v0, v2, v1, v3}, Lax/nd/faceunlock/FaceAuthBridge;->startAuthenticate(IILjava/lang/Object;)V
    :cond_0
    return-void
.end method
```

```smali
.method public scheduleEnroll(ILandroid/os/IBinder;[BILandroid/hardware/face/IFaceServiceReceiver;Ljava/lang/String;[ILandroid/view/Surface;ZLandroid/hardware/face/FaceEnrollOptions;)J
    .registers 16
    invoke-static {}, Lax/nd/faceunlock/FaceAuthBridge;->getInstance()Lax/nd/faceunlock/FaceAuthBridge;
    move-result-object v0
    if-eqz v0, :cond_0
    move-object/from16 v1, p8
    invoke-virtual {v0, p4, p5, v1}, Lax/nd/faceunlock/FaceAuthBridge;->startEnroll(ILjava/lang/Object;Landroid/view/Surface;)V
    :cond_0
    const-wide/16 v0, 0x1
    return-wide v0
.end method
```

```smali
.method private scheduleForSensor(ILcom/android/server/biometrics/sensors/BaseClientMonitor;)V
    .registers 3
    return-void
.end method
```

```smali
.method private scheduleForSensor(ILcom/android/server/biometrics/sensors/BaseClientMonitor;Lcom/android/server/biometrics/sensors/ClientMonitorCallback;)V
    .registers 4
    return-void
.end method
```

### 2.4 Compile and add the bridge
1. Save and compile. If you get the 65536 error, stop (see warning 1).
2. Open the jar as a zip and add the bridge `classes.dex` with the **next free
   number** (on CO17: `classes5.dex`, or the next one if MT created another dex).
3. **Do not sign** the jar.
4. Delete `system/framework/oat/arm64/services.odex`, `.vdex`, `.art` and their `.fsv_meta`.

## 3. (Optional) SystemUI
`system_ext/priv-app/SystemUI/SystemUI.apk` → Dex Editor Plus →
`com.android.systemui.biometrics.AuthController`:

```smali
.method public final isFaceAuthEnrolled(I)Z
    .registers 4
    const-string v0, "persist.sys.oplus.isFaceEnrolled"
    const/4 v1, 0x0
    invoke-static {v0, v1}, Landroid/os/SystemProperties;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    return v0
.end method
```

Compile **without signing** and delete `SystemUI/oat/`. If you get a black screen,
restore the original APK.

## 4. Test
1. Flash or reboot.
2. Settings → Password & security → Face → enroll.
3. If you skipped step 3, reboot.
4. Lock and turn the screen on.

adb checks:
- `logcat | grep -E "FaceAuthBridge|nativeloader.*[Mm]eg"`: all 4 libraries load and `Authentication successful` appears.
- `dumpsys face`: shows `FaceProvider/default`.
- `top`: `system_server` is not busy (if it is, the `scheduleForSensor` patch is missing).
- `getprop persist.sys.oplus.isFaceEnrolled`: `1` after enrolling.

## Limitations
- *Convenience* strength: works for unlocking, not for payments or banking apps.
- Without a real HAL, some face options in Settings (eyes open, fill light) do nothing.
