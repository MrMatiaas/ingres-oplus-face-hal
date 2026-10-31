#!/usr/bin/env python3
"""OPlusFace (ryanistr) ported to ColorOS 17 (Android 17): replaces methods of
FaceService, FaceServiceWrapper and FaceProvider so face auth goes through
ax.nd.faceunlock.FaceAuthBridge. Usage: patch_services_smali.py <apktool smali dir>
"""
import sys, re, os

BASE = os.path.join(sys.argv[1], "com/android/server/biometrics/sensors/face")
FP = 'Lcom/android/server/biometrics/sensors/face/aidl/FaceProvider;'
FB = 'Lax/nd/faceunlock/FaceAuthBridge;'
W = 'Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper;'
FS = 'Lcom/android/server/biometrics/sensors/face/FaceService;'


def replace(path, header, body):
    s = open(path).read()
    pat = re.compile(r'^' + re.escape(header) + r'\n.*?^\.end method\n', re.M | re.S)
    s2, n = pat.subn(lambda m: header + '\n' + body.strip('\n') + '\n.end method\n', s)
    assert n == 1, (path, header, n)
    open(path, 'w').write(s2)
    print('ok', os.path.basename(path), header.split(' ')[-1][:60])


# ---------- FaceService ----------
replace(f'{BASE}/FaceService.smali',
        '.method public static getDeclaredInstances()[Ljava/lang/String;', '''
    .registers 3
    const/4 v0, 0x1
    new-array v0, v0, [Ljava/lang/String;
    const-string v1, "default"
    const/4 v2, 0x0
    aput-object v1, v0, v2
    return-object v0''')

# ---------- FaceServiceWrapper ----------
WF = f'{BASE}/FaceService$FaceServiceWrapper.smali'
replace(WF, '.method public registerAuthenticators(Landroid/hardware/face/FaceSensorConfigurations;)V', f'''
    .registers 4
    invoke-super {{p0}}, Landroid/hardware/face/IFaceService$Stub;->registerAuthenticators_enforcePermission()V
    iget-object v0, p0, {W}->this$0:{FS}
    invoke-static {{v0}}, {FS}->-$$Nest$fgetmRegistry({FS})Lcom/android/server/biometrics/sensors/face/FaceServiceRegistry;
    move-result-object v0
    new-instance v1, Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper$$ExternalSyntheticLambda0;
    invoke-direct {{v1, p0, p1}}, Lcom/android/server/biometrics/sensors/face/FaceService$FaceServiceWrapper$$ExternalSyntheticLambda0;-><init>({W}Landroid/hardware/face/FaceSensorConfigurations;)V
    invoke-virtual {{v0, v1}}, Lcom/android/server/biometrics/sensors/face/FaceServiceRegistry;->registerAll(Ljava/util/function/Supplier;)V
    return-void''')

replace(WF, '.method private getProviders(Landroid/hardware/face/FaceSensorConfigurations;)Ljava/util/List;', f'''
    .registers 8
    .annotation system Ldalvik/annotation/Signature;
        value = {{
            "(",
            "Landroid/hardware/face/FaceSensorConfigurations;",
            ")",
            "Ljava/util/List<",
            "Lcom/android/server/biometrics/sensors/face/ServiceProvider;",
            ">;"
        }}
    .end annotation
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {{v0}}, Ljava/util/ArrayList;-><init>()V
    new-instance v1, Landroid/hardware/biometrics/face/SensorProps;
    invoke-direct {{v1}}, Landroid/hardware/biometrics/face/SensorProps;-><init>()V
    new-instance v2, Landroid/hardware/biometrics/common/CommonProps;
    invoke-direct {{v2}}, Landroid/hardware/biometrics/common/CommonProps;-><init>()V
    const/4 v3, 0x1
    iput v3, v2, Landroid/hardware/biometrics/common/CommonProps;->sensorId:I
    iput v3, v2, Landroid/hardware/biometrics/common/CommonProps;->maxEnrollmentsPerUser:I
    iput-object v2, v1, Landroid/hardware/biometrics/face/SensorProps;->commonProps:Landroid/hardware/biometrics/common/CommonProps;
    new-array v2, v3, [Landroid/hardware/biometrics/face/SensorProps;
    const/4 v3, 0x0
    aput-object v1, v2, v3
    new-instance v1, Landroid/util/Pair;
    const-string v4, "default"
    invoke-direct {{v1, v4, v2}}, Landroid/util/Pair;-><init>(Ljava/lang/Object;Ljava/lang/Object;)V
    iget-object v2, p0, {W}->this$0:{FS}
    invoke-static {{v2}}, {FS}->-$$Nest$fgetmFaceProviderFunction({FS})Lcom/android/server/biometrics/sensors/face/FaceService$FaceProviderFunction;
    move-result-object v2
    invoke-interface {{v2, v1, v3}}, Lcom/android/server/biometrics/sensors/face/FaceService$FaceProviderFunction;->getFaceProvider(Landroid/util/Pair;Z){FP}
    move-result-object v2
    invoke-interface {{v0, v2}}, Ljava/util/List;->add(Ljava/lang/Object;)Z
    return-object v0''')

# ---------- FaceProvider ----------
PF = f'{BASE}/aidl/FaceProvider.smali'
replace(PF, '.method private initSensors(Z[Landroid/hardware/biometrics/face/SensorProps;)V', f'''
    .registers 12
    iget-object v0, p0, {FP}->mContext:Landroid/content/Context;
    invoke-static {{v0}}, {FB}->init(Landroid/content/Context;)V
    new-instance v0, Landroid/hardware/biometrics/face/SensorProps;
    invoke-direct {{v0}}, Landroid/hardware/biometrics/face/SensorProps;-><init>()V
    new-instance v1, Landroid/hardware/biometrics/common/CommonProps;
    invoke-direct {{v1}}, Landroid/hardware/biometrics/common/CommonProps;-><init>()V
    const/4 v2, 0x1
    iput v2, v1, Landroid/hardware/biometrics/common/CommonProps;->sensorId:I
    iput v2, v1, Landroid/hardware/biometrics/common/CommonProps;->maxEnrollmentsPerUser:I
    iput-object v1, v0, Landroid/hardware/biometrics/face/SensorProps;->commonProps:Landroid/hardware/biometrics/common/CommonProps;
    const/4 v1, 0x0
    invoke-direct {{p0, v0, v1}}, {FP}->addAidlSensors(Landroid/hardware/biometrics/face/SensorProps;Z)V
    invoke-static {{}}, {FP}->getExtImpl()Lcom/android/server/biometrics/sensors/face/aidl/IFaceProviderExt;
    move-result-object v2
    move-object v3, p0
    iget-object v4, p0, {FP}->mContext:Landroid/content/Context;
    const/4 v1, 0x1
    new-array v5, v1, [Landroid/hardware/biometrics/face/SensorProps;
    const/4 v1, 0x0
    aput-object v0, v5, v1
    iget-object v6, p0, {FP}->mHalInstanceName:Ljava/lang/String;
    iget-object v7, p0, {FP}->mHandler:Landroid/os/Handler;
    invoke-interface/range {{v2 .. v7}}, Lcom/android/server/biometrics/sensors/face/aidl/IFaceProviderExt;->init({FP}Landroid/content/Context;[Landroid/hardware/biometrics/face/SensorProps;Ljava/lang/String;Landroid/os/Handler;)V
    return-void''')


def bridge(header, regs, call, ret='return-void'):
    replace(PF, header, f'''
    .registers {regs}
    invoke-static {{}}, {FB}->getInstance(){FB}
    move-result-object v0
    if-eqz v0, :cond_end
    {call}
    :cond_end
    {ret}''')


bridge('.method public cancelAuthentication(ILandroid/os/IBinder;J)V', 8,
       f'invoke-virtual {{v0}}, {FB}->stopAuthenticate()V')
bridge('.method public cancelEnrollment(ILandroid/os/IBinder;J)V', 8,
       f'invoke-virtual {{v0}}, {FB}->stopEnroll()V')
bridge('.method public scheduleGenerateChallenge(IILandroid/os/IBinder;Landroid/hardware/face/IFaceServiceReceiver;Ljava/lang/String;)V', 9,
       f'invoke-virtual {{v0, p1, p2, p4}}, {FB}->generateChallenge(IILjava/lang/Object;)V')
bridge('.method public scheduleRemove(ILandroid/os/IBinder;IILandroid/hardware/face/IFaceServiceReceiver;Ljava/lang/String;)V', 10,
       f'invoke-virtual {{v0, p4, p3, p5}}, {FB}->remove(IILjava/lang/Object;)V')
bridge('.method public scheduleRevokeChallenge(IILandroid/os/IBinder;Ljava/lang/String;J)V', 10,
       f'const/4 v2, 0x0\n    invoke-virtual {{v0, p1, p2, v2}}, {FB}->revokeChallenge(IILjava/lang/Object;)V')

replace(PF, '.method public getAuthenticatorId(II)J', f'''
    .registers 7
    invoke-static {{}}, {FB}->getInstance(){FB}
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual {{v0}}, {FB}->getAuthenticatorId()J
    move-result-wide v0
    return-wide v0
    :cond_0
    const-wide/16 v0, 0x0
    return-wide v0''')

replace(PF, '.method public getEnrolledFaces(II)Ljava/util/List;', f'''
    .registers 7
    .annotation system Ldalvik/annotation/Signature;
        value = {{
            "(II)",
            "Ljava/util/List<",
            "Landroid/hardware/face/Face;",
            ">;"
        }}
    .end annotation
    invoke-static {{}}, {FB}->getInstance(){FB}
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual {{v0, p1, p2}}, {FB}->getEnrolledFaces(II)Ljava/util/List;
    move-result-object v0
    return-object v0
    :cond_0
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {{v0}}, Ljava/util/ArrayList;-><init>()V
    return-object v0''')

replace(PF, '.method public isHardwareDetected(I)Z', '''
    .registers 3
    const/4 v0, 0x1
    return v0''')

AUTH_BODY = f'''
    invoke-static {{}}, {FB}->getInstance(){FB}
    move-result-object v0
    if-eqz v0, :cond_0
    invoke-virtual/range {{p6 .. p6}}, Landroid/hardware/face/FaceAuthenticateOptions;->getUserId()I
    move-result v1
    invoke-virtual/range {{p6 .. p6}}, Landroid/hardware/face/FaceAuthenticateOptions;->getSensorId()I
    move-result v2
    move-object/from16 v3, p5
    invoke-virtual {{v0, v2, v1, v3}}, {FB}->startAuthenticate(IILjava/lang/Object;)V
    :cond_0'''
replace(PF, '.method public scheduleAuthenticate(Landroid/os/IBinder;JILcom/android/server/biometrics/sensors/ClientMonitorCallbackConverter;Landroid/hardware/face/FaceAuthenticateOptions;ZIZ)J',
        '    .registers 20' + AUTH_BODY + '\n    const-wide/16 v0, 0x1\n    return-wide v0')
replace(PF, '.method public scheduleAuthenticate(Landroid/os/IBinder;JILcom/android/server/biometrics/sensors/ClientMonitorCallbackConverter;Landroid/hardware/face/FaceAuthenticateOptions;JZIZ)V',
        '    .registers 22' + AUTH_BODY + '\n    return-void')

replace(PF, '.method public scheduleEnroll(ILandroid/os/IBinder;[BILandroid/hardware/face/IFaceServiceReceiver;Ljava/lang/String;[ILandroid/view/Surface;ZLandroid/hardware/face/FaceEnrollOptions;)J', f'''
    .registers 16
    invoke-static {{}}, {FB}->getInstance(){FB}
    move-result-object v0
    if-eqz v0, :cond_0
    move-object/from16 v1, p8
    invoke-virtual {{v0, p4, p5, v1}}, {FB}->startEnroll(ILjava/lang/Object;Landroid/view/Surface;)V
    :cond_0
    const-wide/16 v0, 0x1
    return-wide v0''')

# Sin HAL: no encolar nada en el scheduler (evita bucle infinito de FaceStartUserClient)
replace(PF, '.method private scheduleForSensor(ILcom/android/server/biometrics/sensors/BaseClientMonitor;)V', '''
    .registers 3
    return-void''')
replace(PF, '.method private scheduleForSensor(ILcom/android/server/biometrics/sensors/BaseClientMonitor;Lcom/android/server/biometrics/sensors/ClientMonitorCallback;)V', '''
    .registers 4
    return-void''')
