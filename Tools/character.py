import math
import numpy as np
from geometry import *
from unity_writer import *

BONES=[('Root',None,(0,0,0)),('Hips','Root',(0,.96,0)),('Spine','Hips',(0,1.10,0)),('Chest','Spine',(0,1.30,0)),('Neck','Chest',(0,1.51,0)),('Head','Neck',(0,1.62,0))]
for side,s in [('Left',-1),('Right',1)]:
    BONES += [(side+'Shoulder','Chest',(s*.12,1.42,0)),(side+'UpperArm',side+'Shoulder',(s*.22,1.42,0)),(side+'LowerArm',side+'UpperArm',(s*.49,1.42,0)),(side+'Hand',side+'LowerArm',(s*.72,1.42,0)),(side+'UpperLeg','Hips',(s*.10,.91,0)),(side+'LowerLeg',side+'UpperLeg',(s*.10,.50,.012)),(side+'Foot',side+'LowerLeg',(s*.10,.11,.035)),(side+'Toes',side+'Foot',(s*.10,.07,.17))]
BI={b[0]:i for i,b in enumerate(BONES)}

def loft(rings,segments=28,opening=0):
    # rings: y, x-radius, z-radius, x-offset, z-offset
    m=Mesh(); start=opening/2;end=math.tau-opening/2
    for i in range(len(rings)-1):
      for j in range(segments):
        ids=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)];pts=[];ns=[]
        for k,q in ids:
            y,rx,rz,cx,cz=rings[k];a=start+(end-start)*q/segments
            ripple=1+.015*math.sin(a*7+k*2.4)
            pts.append([cx+rx*math.sin(a)*ripple,y,cz+rz*math.cos(a)*ripple])
            lo=rings[max(0,k-1)];hi=rings[min(len(rings)-1,k+1)];dy=max(hi[0]-lo[0],1e-6)
            tangent=np.array([rx*math.cos(a),0,-rz*math.sin(a)])
            up=np.array([((hi[1]-lo[1])*math.sin(a)+hi[3]-lo[3])/dy,1,((hi[2]-lo[2])*math.cos(a)+hi[4]-lo[4])/dy])
            v=np.cross(tangent,up);v/=max(np.linalg.norm(v),1e-8);ns.append(v.tolist())
        m.tri(pts[0],pts[2],pts[1],normals=[ns[0],ns[2],ns[1]])
        m.tri(pts[0],pts[3],pts[2],normals=[ns[0],ns[3],ns[2]])
    return m

def create_character(game,parent_movement_id):
    visual=Node('EliasCalder',game,layer=8,static=False)
    bone_nodes={};positions={b[0]:np.array(b[2]) for b in BONES}
    for name,parent,p in BONES:
        local=np.array(p)-(positions[parent] if parent else np.zeros(3))
        bone_nodes[name]=Node(name,bone_nodes.get(parent,visual),local,layer=8,static=False)
    groups={}
    def add(mat,mesh,bone,pos=(0,0,0),scale=(1,1,1),rot=(0,0,0),blend=None):
        target=groups.setdefault(mat,Mesh());old=len(target.v);target.merge(mesh,pos,scale,rot)
        for v in target.v[old:]:
            if blend:
                b1,b2,w=blend(v);target.weights.append([BI[b1],BI[b2],1-w,w])
            else:target.weights.append([BI[bone],BI[bone],1,0])
    skin='M_CharacterSkin'; jacket='M_CharacterClothes'; hair='M_Hair';dark='M_RV_Rubber'
    torso=[(.94,.158,.101,0,0),(1.01,.165,.110,0,0),(1.13,.175,.116,0,0),(1.27,.190,.121,0,0),(1.37,.213,.116,0,0),(1.425,.178,.096,0,0),(1.47,.066,.062,0,0),(1.491,.043,.043,0,0)]
    blendtorso=lambda v:('Spine','Chest',float(np.clip((v[1]-1.08)/.26,0,1)))
    add(jacket,loft(torso,36,.38),'Chest',blend=blendtorso)
    add('M_Shirt',loft([(y,rx*.91,rz*.97,x,z) for y,rx,rz,x,z in torso],32),'Chest',blend=blendtorso)
    add(skin,ellipsoid((.080,.12,.083)), 'Neck',(0,1.485,0))
    # Shaped cranium, cheek planes, angular jaw, ears and a distinct hooked nose.
    add(skin,ellipsoid((.197,.239,.193),20,32),'Head',(0,1.649,.010))
    add(skin,ellipsoid((.146,.101,.150),14,24),'Head',(0,1.563,.029))
    for s in [-1,1]:
        add(skin,ellipsoid((.032,.061,.035),12,16),'Head',(s*.101,1.637,.007))
        add(skin,ellipsoid((.052,.035,.028),12,18),'Head',(s*.054,1.615,.077))
        add('M_EyeWhite',ellipsoid((.034,.013,.012),10,18),'Head',(s*.044,1.653,.101))
        add('M_Iris',ellipsoid((.010,.010,.006),10,14),'Head',(s*.044,1.653,.108))
        add(skin,ellipsoid((.041,.010,.013),8,16),'Head',(s*.044,1.642,.101))
        add(hair,ellipsoid((.044,.008,.013),8,16),'Head',(s*.043,1.674,.099),rot=(0,0,-s*8))
        # Fine rectangular spectacle rims, bridge and side arms.
        x=s*.045
        frame=[(x-.033,1.671,.116),(x+.033,1.671,.116),(x+.034,1.640,.116),(x-.033,1.640,.116),(x-.033,1.671,.116)]
        add('M_DarkMetal',tube(frame,.0027,8),'Head')
        add('M_DarkMetal',tube([(s*.078,1.661,.114),(s*.10,1.661,.080),(s*.106,1.657,-.02)],.0025,8),'Head')
    add('M_DarkMetal',tube([(-.011,1.660,.116),(0,1.664,.12),(.011,1.660,.116)],.0025,8),'Head')
    add(skin,ellipsoid((.028,.063,.039),14,18),'Head',(.003,1.638,.112),rot=(-13,0,0))
    add(skin,ellipsoid((.039,.021,.031),10,18),'Head',(.003,1.614,.133))
    add(hair,ellipsoid((.062,.010,.016),8,20),'Head',(0,1.597,.105))
    add(hair,ellipsoid((.048,.041,.015),12,20),'Head',(0,1.568,.099))
    add(skin,tube([(-.024,1.586,.11),(0,1.583,.114),(.025,1.586,.108)],.0024,8),'Head')
    # Lapels, chest pockets, seam binding, jacket buttons and shirt collar.
    for s in [-1,1]:
        lapel=Mesh();lapel.quad((s*.027,1.42,.09),(s*.090,1.395,.118),(s*.063,1.24,.131),(s*.028,1.31,.132))
        if s<0:lapel.t=[v for i in range(0,len(lapel.t),3) for v in [lapel.t[i],lapel.t[i+2],lapel.t[i+1]]]
        add(jacket,lapel,'Chest')
        add(jacket,box((.075,.062,.012),.005),'Chest',(s*.117,1.283,.114))
        add('M_Wood',cylinder(.0035,.004,10),'Chest',(s*.117,1.306,.126),rot=(90,0,0))
    for y in [1.04,1.12,1.20,1.28,1.35]:add('M_Paper',ellipsoid((.004,.004,.004),6,8),'Spine',(0,y,.118))
    add(dark,loft([(.929,.166,.107,0,0),(.956,.167,.108,0,0)],32),'Hips')
    add('M_Trousers',loft([(.84,.16,.095,0,0),(.90,.175,.108,0,0),(.948,.163,.104,0,0)],32),'Hips')
    add('M_Metal',box((.034,.026,.008),.002),'Hips',(0,.941,.114))
    # Articulated sleeves and trouser legs include weighted joint transition bands.
    for side,s in [('Left',-1),('Right',1)]:
        arm=loft([(-.085,.003,.003,0,0),(-.055,.057,.055,0,0),(0,.078,.076,0,0),(.08,.078,.077,0,0),(.20,.066,.064,0,0),(.29,.062,.060,0,0),(.36,.059,.056,0,0),(.46,.051,.049,0,0),(.51,.048,.045,0,0)],26)
        def armblend(v,sd=side,sg=s):return (sd+'UpperArm',sd+'LowerArm',float(np.clip((abs(v[0])-.43)/.12,0,1)))
        add(jacket,arm,side+'UpperArm',(s*.20,1.42,0),rot=(0,0,-s*90),blend=armblend)
        add(jacket,cylinder(.048,.025,22),side+'LowerArm',(s*.705,1.42,0),rot=(0,0,90))
        add(skin,ellipsoid((.10,.048,.079),12,20),side+'Hand',(s*.765,1.419,.004))
        for j in range(4):
            add(skin,ellipsoid((.071,.012,.014),10,12),side+'Hand',(s*.815,1.416,(j-1.5)*.018))
        add(skin,ellipsoid((.046,.022,.023),10,12),side+'Hand',(s*.767,1.396,.052),rot=(0,s*25,0))
        leg=loft([(.105,.062,.066,s*.1,.005),(.20,.066,.068,s*.1,0),(.38,.072,.076,s*.1,0),(.49,.074,.080,s*.1,.012),(.56,.080,.086,s*.1,0),(.76,.088,.092,s*.1,0),(.93,.090,.10,s*.1,0)],28)
        def legblend(v,sd=side):return(sd+'LowerLeg',sd+'UpperLeg',float(np.clip((v[1]-.44)/.14,0,1)))
        add('M_Trousers',leg,side+'UpperLeg',blend=legblend)
        add(dark,ellipsoid((.133,.123,.255),14,24),side+'Foot',(s*.1,.080,.078))
        add(dark,box((.125,.027,.235),.009),side+'Foot',(s*.1,.023,.078))
        for z in [.056,.085,.111]:add('M_Wood',tube([(s*.1-.033,.139,z),(s*.1+.033,.139,z)],.003,6),side+'Foot')
    add(dark,cylinder(.052,.027,22),'LeftLowerArm',(-.682,1.42,0),rot=(0,0,90))
    add('M_Chrome',box((.030,.012,.032),.004),'LeftLowerArm',(-.68,1.472,0))
    add('M_EyeWhite',box((.021,.002,.024),.002),'LeftLowerArm',(-.68,1.480,0))
    for mat,mesh in groups.items():
        name='EliasCalder_'+mat[2:];path=save_mesh(name,mesh,'Characters/EliasCalder',bones=[b[2] for b in BONES])
        n=Node(name,visual,layer=8,static=False);n.mesh=name;n.mat=mat
        n.skinBones=[bone_nodes[b[0]].id for b in BONES]
        body=renderer_body(MATERIALS[mat])+f'''  m_Quality: 4
  m_UpdateWhenOffscreen: 0
  m_SkinnedMotionVectors: 1
  m_Mesh: {ref(path)}
  m_Bones:
'''+''.join(f'  - {{fileID: {bone_nodes[b[0]].tid}}}\n' for b in BONES)+f'''  m_BlendShapeWeights: []
  m_RootBone: {{fileID: {bone_nodes['Hips'].tid}}}
  m_AABB:
    m_Center: {{x: 0, y: 0.9, z: 0}}
    m_Extent: {{x: 1, y: 1.1, z: 0.7}}
  m_DirtyAABB: 0
'''
        n.component(137,body)
    controller='Assets/_DesertShift/Animations/Character/AC_EliasCalder.controller'
    aid=visual.component(95,f'''  m_Enabled: 1
  m_Avatar: {{fileID: 0}}
  m_Controller: {ref(controller,9100000)}
  m_CullingMode: 0
  m_UpdateMode: 0
  m_ApplyRootMotion: 0
  m_LinearVelocityBlending: 0
  m_StabilizeFeet: 1
  m_WarningMessage: 
  m_HasTransformHierarchy: 1
  m_AllowConstantClipSamplingOptimization: 1
  m_KeepAnimatorStateOnDisable: 0
  m_WriteDefaultValuesOnDisable: 0
''')
    mapping='  humanBones:\n'
    for name,_,_ in BONES:
        if name!='Root':mapping+=f'  - humanName: {name}\n    bone: {{fileID: {bone_nodes[name].tid}}}\n'
    visual.script('CharacterRig',mapping+f'  animator: {{fileID: {aid}}}\n')
    visual.script('PlayerAnimator',f'  movement: {{fileID: {parent_movement_id}}}\n  animator: {{fileID: {aid}}}\n')
    # Comfortable standing pose is visible in the editor before Play.
    bone_nodes['LeftUpperArm'].rot=[0,0,78];bone_nodes['RightUpperArm'].rot=[0,0,-78]
    return visual,bone_nodes

def anim_pose(name,t):
    d={b[0]:[0.,0.,0.] for b in BONES};hip=.96
    d['LeftUpperArm'][2]=78;d['RightUpperArm'][2]=-78
    walk=name in ['WalkForward','WalkBackward','StrafeLeft','StrafeRight','Jog','Run','CrouchWalk']
    crouch=name.startswith('Crouch');amp=28 if name=='Run' else 21 if name=='Jog' else 15
    if walk:
        s=math.sin(t*math.tau);c=math.cos(t*math.tau)
        if name=='WalkBackward':s=-s
        for side,sg in [('Left',1),('Right',-1)]:
            d[side+'UpperLeg'][0]=s*amp*sg
            d[side+'LowerLeg'][0]=max(0,-s*sg)*(44 if name=='Run' else 29)
            d[side+'Foot'][0]=-s*7*sg
            d[side+'UpperArm'][0]=-s*amp*.75*sg
            d[side+'LowerArm'][1]=(18 if name in ['Run','Jog'] else 8)*sg
        d['Spine'][1]=s*3.0;hip+=abs(c)*(.025 if name=='Run' else .015)
        if name.startswith('Strafe'):
            for side in ['Left','Right']:d[side+'UpperLeg'][2]=s*13
    else:
        d['Chest'][0]=math.sin(t*math.tau)*.7
        d['Head'][1]=math.sin(t*math.tau)*1.5
    if crouch:
        hip-=.40;d['Spine'][0]=19;d['Chest'][0]=9;d['Head'][0]=-15
        for side in ['Left','Right']:
            d[side+'UpperLeg'][0]-=47;d[side+'LowerLeg'][0]+=77;d[side+'Foot'][0]-=30
    if name in ['JumpStart','JumpLoop','JumpLand']:
        amount=math.sin(t*math.pi) if name!='JumpLoop' else 1
        d['Spine'][0]=amount*9
        for side in ['Left','Right']:
            d[side+'UpperLeg'][0]=-amount*24;d[side+'LowerLeg'][0]=amount*47
            d[side+'UpperArm'][0]=-amount*32
        if name=='JumpLand':hip-=amount*.13
    if name in ['TurnLeft','TurnRight']:
        d['Spine'][1]=(-1 if name=='TurnLeft' else 1)*8*math.sin(t*math.pi)
        d['LeftUpperLeg'][0]=math.sin(t*math.tau)*8;d['RightUpperLeg'][0]=-math.sin(t*math.tau)*8
    return d,hip

CLIPS={'Idle':2.8,'WalkForward':1.05,'WalkBackward':1.15,'StrafeLeft':1.1,'StrafeRight':1.1,'Jog':.78,'Run':.60,'CrouchIdle':2.8,'CrouchWalk':1.3,'JumpStart':.16,'JumpLoop':.7,'JumpLand':.22,'TurnLeft':.75,'TurnRight':.75}
def build_animations():
    parents={b[0]:b[1] for b in BONES}
    def bp(name):return bp(parents[name])+'/'+name if parents[name] else name
    for name,duration in CLIPS.items():
        path=f'Assets/_DesertShift/Animations/Character/{name}.anim';loop=not name.startswith('Jump') or name=='JumpLoop'
        text=HEAD+f'''--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  serializedVersion: 7
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves:
'''
        times=np.linspace(0,duration,17)
        for bone,_,_ in BONES:
            text+='  - curve:\n      serializedVersion: 2\n      m_Curve:\n'
            for t in times:
                d,h=anim_pose(name,t/duration);q=Rotation.from_euler('xyz',d[bone],degrees=True).as_quat()
                text+=f'''      - serializedVersion: 3
        time: {t:.6f}
        value: {vec(q)}
        inSlope: {{x: 0, y: 0, z: 0, w: 0}}
        outSlope: {{x: 0, y: 0, z: 0, w: 0}}
        tangentMode: 0
        weightedMode: 0
        inWeight: {{x: 0, y: 0, z: 0, w: 0}}
        outWeight: {{x: 0, y: 0, z: 0, w: 0}}
'''
            text+=f'      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: {bp(bone)}\n'
        text+='  m_CompressedRotationCurves: []\n  m_EulerCurves: []\n  m_PositionCurves:\n  - curve:\n      serializedVersion: 2\n      m_Curve:\n'
        for t in times:
            d,h=anim_pose(name,t/duration)
            text+=f'''      - serializedVersion: 3
        time: {t:.6f}
        value: {{x: 0, y: {h:.7f}, z: 0}}
        inSlope: {{x: 0, y: 0, z: 0}}
        outSlope: {{x: 0, y: 0, z: 0}}
        tangentMode: 0
        weightedMode: 0
        inWeight: {{x: 0, y: 0, z: 0}}
        outWeight: {{x: 0, y: 0, z: 0}}
'''
        text+=f'''      m_PreInfinity: 2
      m_PostInfinity: 2
      m_RotationOrder: 4
    path: Root/Hips
  m_ScaleCurves: []
  m_FloatCurves: []
  m_PPtrCurves: []
  m_SampleRate: 30
  m_WrapMode: 0
  m_Bounds:
    m_Center: {{x: 0, y: 0.9, z: 0}}
    m_Extent: {{x: 1, y: 1.1, z: 0.6}}
  m_ClipBindingConstant:
    genericBindings: BINDINGS_PLACEHOLDER
    pptrCurveMapping: []
  m_AnimationClipSettings:
    serializedVersion: 2
    m_AdditiveReferencePoseClip: {{fileID: 0}}
    m_AdditiveReferencePoseTime: 0
    m_StartTime: 0
    m_StopTime: {duration}
    m_OrientationOffsetY: 0
    m_Level: 0
    m_CycleOffset: 0
    m_HasAdditiveReferencePose: 0
    m_LoopTime: {int(loop)}
    m_LoopBlend: {int(loop)}
    m_LoopBlendOrientation: 0
    m_LoopBlendPositionY: 0
    m_LoopBlendPositionXZ: 0
    m_KeepOriginalOrientation: 1
    m_KeepOriginalPositionY: 1
    m_KeepOriginalPositionXZ: 1
    m_HeightFromFeet: 0
    m_Mirror: 0
  m_EditorCurves: []
  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events: []
'''
        import zlib
        bindings='\n'
        for bone,attribute in [(b[0],2) for b in BONES]+[('Hips',1)]:
            ph=zlib.crc32(bp(bone).encode()) & 0xffffffff
            bindings+=f'''    - serializedVersion: 2
      path: {ph}
      attribute: {attribute}
      script: {{fileID: 0}}
      typeID: 4
      customType: 0
      isPPtrCurve: 0
      isIntCurve: 0
      isSerializeReferenceCurve: 0
'''
        text=text.replace(' BINDINGS_PLACEHOLDER',bindings.rstrip())
        write(path,text);meta(path,'NativeFormatImporter','  mainObjectFileID: 7400000\n')
    # Native Animator Controller: directional locomotion tree, crouch tree, jump chain, turns.
    path='Assets/_DesertShift/Animations/Character/AC_EliasCalder.controller'
    c=HEAD+'''--- !u!91 &9100000
AnimatorController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: AC_EliasCalder
  serializedVersion: 5
  m_AnimatorParameters:
'''
    for name,typ in [('Speed',1),('MoveX',1),('MoveY',1),('Turn',1),('VerticalSpeed',1),('Crouch',4),('Grounded',4),('Jump',9),('Land',9)]:
        c+=f'  - m_Name: {name}\n    m_Type: {typ}\n    m_DefaultFloat: 0\n    m_DefaultInt: 0\n    m_DefaultBool: {1 if name=="Grounded" else 0}\n    m_Controller: {{fileID: 9100000}}\n'
    c+='''  m_AnimatorLayers:
  - serializedVersion: 5
    m_Name: Base Layer
    m_StateMachine: {fileID: 1107000000}
    m_Mask: {fileID: 0}
    m_Motions: []
    m_Behaviours: []
    m_BlendingMode: 0
    m_SyncedLayerIndex: -1
    m_DefaultWeight: 1
    m_IKPass: 0
    m_SyncedLayerAffectsTiming: 0
    m_Controller: {fileID: 9100000}
'''
    states=['Locomotion','Crouching','JumpStart','JumpLoop','JumpLand','TurnLeft','TurnRight'];sid={s:1102000000+i for i,s in enumerate(states)}
    transitions=[]
    def trans(src,dst,conditions=[],exit_time=None):
        tid=1101000000+len(transitions);transitions.append((tid,src,dst,conditions,exit_time));return tid
    trans('Locomotion','Crouching',[(1,'Crouch',0)]);trans('Crouching','Locomotion',[(2,'Crouch',0)])
    trans('Locomotion','JumpStart',[(1,'Jump',0)]);trans('Locomotion','JumpLoop',[(2,'Grounded',0)])
    trans('Crouching','JumpLoop',[(2,'Grounded',0)])
    trans('JumpStart','JumpLoop',[],.9);trans('JumpLoop','JumpLand',[(1,'Grounded',0)])
    trans('JumpLand','Locomotion',[],.92)
    for name,mode in [('TurnLeft',4),('TurnRight',3)]:
        trans('Locomotion',name,[(mode,'Turn',-35 if mode==4 else 35),(4,'Speed',.1)])
        trans(name,'Locomotion',[],.8)
    c+='''--- !u!1107 &1107000000
AnimatorStateMachine:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: Base Layer
  m_ChildStates:
'''
    for i,s in enumerate(states):c+=f'  - serializedVersion: 1\n    m_State: {{fileID: {sid[s]}}}\n    m_Position: {{x: {220+(i%3)*220}, y: {80+(i//3)*100}, z: 0}}\n'
    c+=f'''  m_ChildStateMachines: []
  m_AnyStateTransitions: []
  m_EntryTransitions: []
  m_StateMachineTransitions: {{}}
  m_StateMachineBehaviours: []
  m_AnyStatePosition: {{x: 20, y: 20, z: 0}}
  m_EntryPosition: {{x: 20, y: 100, z: 0}}
  m_ExitPosition: {{x: 900, y: 100, z: 0}}
  m_ParentStateMachinePosition: {{x: 900, y: 20, z: 0}}
  m_DefaultState: {{fileID: {sid['Locomotion']}}}
'''
    for s in states:
        motion='{fileID: 2060000000}' if s=='Locomotion' else '{fileID: 2060000001}' if s=='Crouching' else ref(f'Assets/_DesertShift/Animations/Character/{s}.anim',7400000)
        tids=[t[0] for t in transitions if t[1]==s]
        c+=f'''--- !u!1102 &{sid[s]}
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {s}
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions:
'''+''.join(f'  - {{fileID: {t}}}\n' for t in tids)+f'''  m_StateMachineBehaviours: []
  m_Position: {{x: 50, y: 50, z: 0}}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {motion}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
'''
    for tid,src,dst,conds,et in transitions:
        c+=f'''--- !u!1101 &{tid}
AnimatorStateTransition:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: 
  m_Conditions:{'' if conds else ' []'}
'''
        for mode,param,threshold in conds:c+=f'  - m_ConditionMode: {mode}\n    m_ConditionEvent: {param}\n    m_EventTreshold: {threshold}\n'
        c+=f'''  m_DstStateMachine: {{fileID: 0}}
  m_DstState: {{fileID: {sid[dst]}}}
  m_Solo: 0
  m_Mute: 0
  m_IsExit: 0
  serializedVersion: 3
  m_TransitionDuration: 0.14
  m_TransitionOffset: 0
  m_ExitTime: {et or 0}
  m_HasExitTime: {int(et is not None)}
  m_HasFixedDuration: 1
  m_InterruptionSource: 0
  m_OrderedInterruption: 1
  m_CanTransitionToSelf: 0
'''
    for idx,children,bt in [(0,[('Idle',0,0),('WalkForward',0,2.15),('WalkBackward',0,-2.15),('StrafeLeft',-2.15,0),('StrafeRight',2.15,0),('Jog',0,3.6),('Run',0,6.4)],2),(1,[('CrouchIdle',0,0),('CrouchWalk',1.25,0)],0)]:
        c+=f'''--- !u!206 &{2060000000+idx}
BlendTree:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {'Directional Locomotion' if idx==0 else 'Crouch Blend'}
  m_Childs:
'''
        for nm,x,y in children:c+=f'''  - serializedVersion: 2
    m_Motion: {ref('Assets/_DesertShift/Animations/Character/'+nm+'.anim',7400000)}
    m_Threshold: {x}
    m_Position: {{x: {x}, y: {y}}}
    m_TimeScale: 1
    m_CycleOffset: 0
    m_DirectBlendParameter: Speed
    m_Mirror: 0
'''
        c+=f'''  m_BlendParameter: {'MoveX' if idx==0 else 'Speed'}
  m_BlendParameterY: MoveY
  m_MinThreshold: 0
  m_MaxThreshold: {6.4 if idx==0 else 1.25}
  m_UseAutomaticThresholds: 0
  m_NormalizedBlendValues: 0
  m_BlendType: {bt}
'''
    write(path,c);meta(path,'NativeFormatImporter','  mainObjectFileID: 9100000\n')
