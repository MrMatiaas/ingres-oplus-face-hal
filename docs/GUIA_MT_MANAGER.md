# Guía: desbloqueo facial en ColorOS 17 con MT Manager

[English version](MT_MANAGER_GUIDE.md)

Versión manual de `legacy-bridge/` (motor facial Megvii/Motorola de
[OPlusFace](https://github.com/ryanistr/OPlusFace) dentro de `system_server`),
adaptada a ColorOS 17 / Android 17. Probado en Poco F4 GT (`ingres`).

> **Antes de empezar, dos avisos**
>
> 1. **Límite de 64K en `services.jar`.** El `classes.dex` de CO17 está justo en el
>    límite de 65 536 referencias a métodos y los parches lo superan por unas 10.
>    `build.sh` lo resuelve moviendo las 3 clases parcheadas a un dex nuevo. Si MT
>    Manager da error de *too many method references* / 65536 al compilar, usa
>    `legacy-bridge/build.sh` en un PC.
> 2. **El parche de SystemUI es opcional y arriesgado con MT.** El APK solo tiene
>    firma v2; si al guardarlo se pierde el bloque de firma, SystemUI no carga
>    (pantalla negra). Sin ese parche todo funciona: solo hay que **reiniciar una vez
>    después de registrar la cara**.

## 0. Requisitos
- Root y MT Manager con **Editor Dex Plus**.
- Copia de seguridad de `services.jar` y de `system/framework/oat/arm64/services.*`.
- Del historial de OPlusFace (carpeta `Compiled/`, commit anterior a `10be794`). No se distribuyen aquí, son propietarios:
  - `classes.dex` del puente (igual que `AUTOPATCH/faceunlock/classes.dex`)
  - `libmegface.so`, `libFaceDetectCA.so`, `libMegviiUnlock.so`, `libMegviiUnlock-jni-1.2.so`
  - `model_file`, `panorama_mgb`, `init.universal-face.rc`

Rutas: en un árbol de DNA, `.../system/system/...`; en el sistema montado, `/system/...`.

## 1. Copiar archivos

| Archivo | Destino | Permisos |
|---|---|---|
| los 4 `.so` | `system/lib64/` | 644 |
| `model_file`, `panorama_mgb` | `system/etc/face/` (crear, 755) | 644 |
| `init.universal-face.rc` | `system/etc/init/` | 644 |

Si compilas con DNA, añade al final de `config/system_fs_config`:

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

y al final de `config/system_file_contexts`:

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

## 2. Parchear `services.jar`
Abre `system/framework/services.jar` en MT → **Editor Dex Plus** → selecciona **todos**
los `classes*.dex`. En cada caso sustituye **el método entero** (de `.method` a
`.end method`).

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
`registerAuthenticators` deja de abortar sin HAL y `getProviders` crea el sensor
`default` con `SensorProps` falsos.

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
Hay 14 métodos; ojo, hay dos `scheduleAuthenticate` y dos `scheduleForSensor` con firmas distintas.
**Los dos `scheduleForSensor` vacíos son imprescindibles**: sin ellos
`FaceStartUserClient` reintenta sin fin y `system_server` se queda al ~80 % de CPU.

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

### 2.4 Compilar y añadir el puente
1. Guarda y compila. Si da error de 65536, para (ver aviso 1).
2. Abre el jar como zip y añade el `classes.dex` del puente con el **siguiente número
   libre** (en CO17: `classes5.dex`, o el siguiente si MT creó otro dex).
3. **No firmes** el jar.
4. Borra `system/framework/oat/arm64/services.odex`, `.vdex`, `.art` y sus `.fsv_meta`.

## 3. (Opcional) SystemUI
`system_ext/priv-app/SystemUI/SystemUI.apk` → Editor Dex Plus →
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

Compila **sin firmar** y borra `SystemUI/oat/`. Si sale pantalla negra, restaura el
APK original.

## 4. Probar
1. Flashea o reinicia.
2. Ajustes → Contraseña y seguridad → Cara → registra la cara.
3. Si no hiciste el paso 3, reinicia.
4. Bloquea y enciende la pantalla.

Comprobaciones por adb:
- `logcat | grep -E "FaceAuthBridge|nativeloader.*[Mm]eg"`: cargan las 4 librerías y aparece `Authentication successful`.
- `dumpsys face`: aparece `FaceProvider/default`.
- `top`: `system_server` sin consumo alto (si lo hay, falta el parche de `scheduleForSensor`).
- `getprop persist.sys.oplus.isFaceEnrolled`: vale `1` tras registrar.

## Limitaciones
- Nivel de seguridad *convenience*: sirve para desbloquear, no para pagos ni apps bancarias.
- Sin HAL real, algunas opciones de cara de Ajustes (ojos abiertos, luz de relleno) no hacen nada.
