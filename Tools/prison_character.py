"""Original smooth articulated prison population, in metres, with continuous UVs."""
import math
import numpy as np
from geometry import *
from unity_writer import *
BONES=[('Root',None,(0,0,0)),('Hips','Root',(0,.97,0)),('Spine','Hips',(0,1.10,0)),('Chest','Spine',(0,1.31,0)),('Neck','Chest',(0,1.50,0)),('Head','Neck',(0,1.64,0))]
for side,s in [('Left',-1),('Right',1)]:
 BONES += [(side+'Shoulder','Chest',(s*.13,1.43,0)),(side+'UpperArm',side+'Shoulder',(s*.22,1.43,0)),(side+'LowerArm',side+'UpperArm',(s*.49,1.43,0)),(side+'Hand',side+'LowerArm',(s*.72,1.43,0)),(side+'UpperLeg','Hips',(s*.105,.91,0)),(side+'LowerLeg',side+'UpperLeg',(s*.105,.50,.012)),(side+'Foot',side+'LowerLeg',(s*.105,.105,.03)),(side+'Toes',side+'Foot',(s*.105,.06,.17))]
BONES.append(('Jaw','Head',(0,1.59,.03)))
BI={b[0]:i for i,b in enumerate(BONES)}
# width, belly, skin, clothes, haircut, beard, face, stature
PROFILES={
 'Elias':(1,1,'Olive','PrisonOrange','crop','stubble',0,1),
 'Niko':(.94,.95,'Tan','PrisonGrey','swept','beard',1,1),
 'Malik':(1.16,1.09,'Deep','PrisonBurgundy','buzz','beard',2,1.04),
 'Heavy':(1.34,1.60,'Tan','PrisonSand','bald','moustache',3,1),
 'Lean':(.83,.83,'Light','PrisonGrey','receding','stubble',4,.99),
 'Athletic':(1.14,.98,'Deep','PrisonCream','buzz','none',5,1.045),
 'Rival':(1.13,1.05,'Light','RivalUniform','buzz','stubble',6,1.02),
 'Guard':(1.08,1.08,'Light','GuardUniform','crop','none',7,1.02),
 'Brother':(.89,.92,'Olive','BrotherClothes','swept','none',0,.99),
 'Rafi':(.9,.95,'Brown','PrisonCream','receding','beard',8,.98)}
def loft(rings,segments=32,opening=0):
 m=Mesh();start=opening/2;end=math.tau-opening/2;y0,y1=rings[0][0],rings[-1][0]
 for i in range(len(rings)-1):
  for j in range(segments):
   pts=[];ns=[];uv=[]
   for k,q in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]:
    y,rx,rz,cx,cz=rings[k];a=start+(end-start)*q/segments
    pts.append([cx+rx*math.sin(a),y,cz+rz*math.cos(a)])
    lo=rings[max(0,k-1)];hi=rings[min(len(rings)-1,k+1)];dy=max(hi[0]-lo[0],1e-6)
    tangent=np.array([rx*math.cos(a),0,-rz*math.sin(a)])
    up=np.array([((hi[1]-lo[1])*math.sin(a)+hi[3]-lo[3])/dy,1,((hi[2]-lo[2])*math.cos(a)+hi[4]-lo[4])/dy])
    v=np.cross(tangent,up);v/=max(np.linalg.norm(v),1e-8);ns.append(v.tolist());uv.append((q/segments,(y-y0)/max(y1-y0,.001)))
   for a,b,c in [(0,2,1),(0,3,2)]:m.tri(pts[a],pts[b],pts[c],uvs=[uv[a],uv[b],uv[c]],normals=[ns[a],ns[b],ns[c]])
 return m
def build_body(profile):
 w,b,sk,cl,cut,beard,face,height=PROFILES[profile];skin='M_Skin'+sk;shirt='M_'+cl;trousers='M_PrisonOrangeTrousers' if profile=='Elias' else 'M_Trousers';hair='M_GreyHair' if profile=='Lean' else 'M_Hair';groups={}
 def add(mat,mesh,bone,pos=(0,0,0),scale=(1,1,1),rot=(0,0,0),blend=None):
  target=groups.setdefault(mat,Mesh());old=len(target.v);target.merge(mesh,pos,scale,rot)
  for v in target.v[old:]:
   if blend:
    b1,b2,t=blend(v);target.weights.append([BI[b1],BI[b2],1-t,t])
   else:target.weights.append([BI[bone],BI[bone],1,0])
 torso=[(.967,.16*w,.103*min(b,1.2),0,0),(1.02,.167*w,.118*b,0,.011*(b-1)),(1.13,.175*w,.117*b,0,.02*(b-1)),(1.27,.198*w,.117*min(b,1.15),0,0),(1.37,.22*w,.108,0,0),(1.425,.221*w,.097,0,0),(1.452,.165*w,.080,0,0),(1.465,.071,.062,0,0),(1.478,.052,.048,0,0)]
 bt=lambda v:('Spine','Chest',float(np.clip((v[1]-1.07)/.26,0,1)))
 add(shirt,loft(torso,40),'Chest',blend=bt)
 add('M_Undershirt',box((.07,.065,.006),.002),'Chest',(0,1.434,.071),rot=(12,0,0))
 for s in [-1,1]:add(shirt,box((.055,.026,.013),.002),'Chest',(s*.063,1.423,.09),rot=(0,0,s*24))
 add(shirt,box((.077,.076,.008),.002),'Chest',(-.10*w,1.296,.117))
 add('M_Seam',tube([(-.138*w,1.26,.124),(-.102*w,1.259,.127),(-.063*w,1.26,.124)],.0015,6),'Chest')
 if profile!='Elias':add('M_PrisonPatch',box((.073,.031,.006),.001),'Chest',(.103*w,1.318,.117))
 else:
  # Printed inmate identification follows the shirt instead of floating over it.
  def print_panel(cx,cy,width,height,back=False):
   m=Mesh()
   for k in range(8):
    for j in range(12):
     ps=[];uvs=[]
     for u,v in [(j/12,k/8),((j+1)/12,k/8),((j+1)/12,(k+1)/8),(j/12,(k+1)/8)]:
      x=cx+(u-.5)*width;y=cy+(v-.5)*height
      rx=np.interp(y,[r[0] for r in torso],[r[1] for r in torso]);rz=np.interp(y,[r[0] for r in torso],[r[2] for r in torso])
      # Subdivide across both shirt axes and clear its 1.8 mm cloth folds.
      z=(rz*math.sqrt(max(.05,1-(x/rx)**2))+.004)*(-1 if back else 1)
      ps.append((x,y,z));uvs.append((u if back else 1-u,v))
     if back:m.quad(*ps[::-1],uv=uvs[::-1])
     else:m.quad(*ps,uv=uvs)
   return m
  add('M_EliasFrontID',print_panel(.101,1.318,.093,.038),'Chest',blend=bt)
  add('M_EliasBackID',print_panel(0,1.30,.28,.135,True),'Chest',blend=bt)
 add('M_Seam',tube([(-.15*w,.987,.051),(-.115*w,.972,.09),(0,.968,.108*b),(.115*w,.972,.09),(.15*w,.987,.051)],.002,6),'Spine')
 add(skin,loft([(1.46,.047,.044,0,0),(1.5,.047,.045,0,0),(1.548,.054,.046,0,0)],28),'Neck')
 fw=1+(face%3-1)*.055;jaw=.078 if face in [2,5,6] else .069 if face==4 else .074
 head=[(1.527,.040,.041,0,.025),(1.546,jaw*.74,.055,0,.026),(1.571,jaw,.066,0,.024),(1.605,.085*fw,.072,0,.017),(1.645,.097*fw,.074,0,.010),(1.682,.095*fw,.080,0,.005),(1.726,.092*fw,.081,0,0),(1.762,.072*fw,.064,0,-.003),(1.786,.035,.030,0,-.004),(1.791,.004,.004,0,-.004)]
 add(skin,loft(head,48),'Head',blend=lambda v:('Jaw','Head',float(np.clip((v[1]-1.57)/.06,0,1))))
 for s in [-1,1]:
  add(skin,ellipsoid((.036,.063,.029),16,20),'Head',(s*.097*fw,1.647,.002))
  add('M_SkinCrease',ellipsoid((.014,.034,.01),10,16),'Head',(s*.111*fw,1.65,.007))
  x=s*.041*fw;z=.077
  add(skin,ellipsoid((.042,.021,.016),12,20),'Head',(x,1.671,z))
  add('M_EyeWhite',ellipsoid((.032,.010,.014),12,24),'Head',(x,1.672,z+.009))
  add('M_Iris',ellipsoid((.009,.010,.005),12,18),'Head',(x,1.672,z+.017))
  add('M_Pupil',ellipsoid((.005,.006,.003),10,14),'Head',(x,1.672,z+.020))
  add('M_EyeWhite',ellipsoid((.002,.002,.002),6,8),'Head',(x-.002,1.674,z+.022))
  add(skin,ellipsoid((.042,.010,.016),10,24),'Head',(x,1.683,z+.008))
  add(skin,ellipsoid((.040,.007,.013),10,24),'Head',(x,1.661,z+.008))
  add(hair,tube([(x-s*.020,1.696,z+.006),(x,1.700,z+.009),(x+s*.021,1.694,z)],.0033,8),'Head')
 add(skin,ellipsoid((.024,.055,.033),16,24),'Head',(0,1.651,.094),rot=(-10,0,0))
 add(skin,ellipsoid((.034,.022,.034),14,24),'Head',(0,1.630,.113))
 for s in [-1,1]:
  add(skin,ellipsoid((.015,.014,.021),12,18),'Head',(s*.014,1.628,.105))
  add('M_SkinCrease',ellipsoid((.008,.003,.009),8,12),'Head',(s*.011,1.622,.113))
 add('M_Lips',ellipsoid((.047,.010,.008),12,28),'Head',(0,1.603,.091))
 add('M_Lips',ellipsoid((.044,.009,.008),12,28),'Jaw',(0,1.594,.093))
 add('M_MouthLine',tube([(-.023,1.600,.096),(0,1.598,.098),(.023,1.600,.096)],.00085,6),'Jaw')
 if beard in ['beard','stubble']:
  bm=Mesh();rings=[(1.536,jaw*.53,.047,.026),(1.551,jaw*.80,.058,.026),(1.571,jaw,.066,.024),(1.590,.081*fw,.070,.020)]
  for k in range(len(rings)-1):
   for i in range(40):
    pts=[];ns=[];uv=[]
    for r,q in [(k,i),(k+1,i),(k+1,i+1),(k,i+1)]:
     y,rx,rz,cz=rings[r];a=-1.4+2.8*q/40
     pts.append([(rx+.0008)*math.sin(a),y,cz+(rz+.0008)*math.cos(a)])
     ns.append([math.sin(a),0,math.cos(a)]);uv.append((q/40,r/3))
    for aa,bb,cc in [(0,2,1),(0,3,2)]:bm.tri(pts[aa],pts[bb],pts[cc],uvs=[uv[aa],uv[bb],uv[cc]],normals=[ns[aa],ns[bb],ns[cc]])
  add('M_Beard'+sk if beard=='beard' else 'M_Stubble'+sk,bm,'Jaw')
 if beard=='moustache':add(hair,ellipsoid((.055,.010,.008),10,28),'Head',(0,1.613,.099))
 if cut!='bald':
  start=1.73 if cut=='receding' else 1.712
  cap=[(start,.096*fw,.079,0,-.005),(1.751,.086*fw,.076,0,-.006),(1.783,.056*fw,.050,0,-.006),(1.801,.008,.008,0,-.006)]
  if cut=='buzz':cap=[(1.733,.088*fw,.073,0,-.006),(1.766,.07*fw,.061,0,-.006),(1.791,.031,.025,0,-.006),(1.797,.004,.004,0,-.006)]
  add(hair,loft(cap,44),'Head')
  if cut in ['crop','swept']:
   for i in range(13):
    x=-.071+i*.012;top=1.792-.04*(abs(x)/.085)**2
    add(hair,tube([(x,top-.034,.052),(x+.002,top-.010,.041),(x+.003,top,.008),(x+.002,top-.025,-.035)],.0028,7),'Head')
  for s in [-1,1]:add(hair,ellipsoid((.012,.055,.042),10,16),'Head',(s*.090*fw,1.693,-.017))
 waist=.160*w
 add(trousers,loft([(.83,waist*.98,.091*min(b,1.2),0,0),(.90,waist*1.05,.102*min(b,1.2),0,0),(.977,waist,.105*min(b,1.2),0,0)],36),'Hips')
 add('M_Belt',loft([(.943,waist+.002,.106*min(b,1.2),0,0),(.964,waist+.002,.106*min(b,1.2),0,0)],36),'Hips')
 add('M_Metal',box((.029,.023,.008),.002),'Hips',(0,.955,.109*min(b,1.2)))
 for side,s in [('Left',-1),('Right',1)]:
  aw=min(w,1.15)
  arm=loft([(-.040,.002,.002,0,0),(-.021,.049*aw,.049*aw,0,0),(0,.070*aw,.069*aw,0,0),(.07,.073*aw,.071*aw,0,0),(.18,.062*aw,.06*aw,0,0),(.215,.059*aw,.059*aw,0,0)],30)
  ba=lambda v,sd=side:(sd+'UpperArm',sd+'LowerArm',float(np.clip((abs(v[0])-.43)/.10,0,1)))
  add(shirt,arm,side+'UpperArm',(s*.22,1.43,0),rot=(0,0,-s*90),blend=ba)
  bare=loft([(.205,.055*aw,.054*aw,0,0),(.28,.054*aw,.051*aw,0,0),(.38,.045*aw,.041*aw,0,0),(.46,.033,.031,0,0),(.52,.029,.027,0,0)],30)
  add(skin,bare,side+'LowerArm',(s*.22,1.43,0),rot=(0,0,-s*90),blend=ba)
  add(shirt,loft([(.201,.061*aw,.060*aw,0,0),(.211,.061*aw,.060*aw,0,0)],28),side+'UpperArm',(s*.22,1.43,0),rot=(0,0,-s*90))
  add(skin,ellipsoid((.087,.043,.070),16,24),side+'Hand',(s*.755,1.43,.005))
  for j in range(4):
   ln=[.051,.064,.06,.046][j];z=(j-1.5)*.015
   add(skin,ellipsoid((ln,.012,.013),12,16),side+'Hand',(s*(.788+ln*.15),1.428,z))
   add('M_Nails',ellipsoid((.013,.002,.008),6,10),side+'Hand',(s*(.791+ln*.48),1.434,z))
  add(skin,ellipsoid((.045,.021,.020),12,18),side+'Hand',(s*.751,1.412,.040),rot=(0,s*22,0))
  lw=min(w,1.23)
  leg=loft([(.106,.053*lw,.056*lw,s*.105,.008),(.18,.056*lw,.060*lw,s*.105,0),(.34,.061*lw,.063*lw,s*.105,0),(.49,.066*lw,.069*lw,s*.105,.012),(.60,.071*lw,.076*lw,s*.105,0),(.77,.079*lw,.081*lw,s*.105,0),(.92,.086*lw,.09*lw,s*.105,0)],34)
  bl=lambda v,sd=side:(sd+'LowerLeg',sd+'UpperLeg',float(np.clip((v[1]-.43)/.15,0,1)))
  add(trousers,leg,side+'UpperLeg',blend=bl)
  add('M_Shoe',ellipsoid((.120,.104,.263),18,28),side+'Foot',(s*.105,.077,.071))
  add('M_Sole',box((.121,.024,.253),.006),side+'Foot',(s*.105,.024,.072))
  add('M_Shoe',ellipsoid((.11,.066,.143),12,24),side+'Foot',(s*.105,.10,.034))
  for z in [.024,.048,.071]:add('M_Laces',tube([(s*.105-.032,.136,z),(s*.105+.032,.136,z)],.002,6),side+'Foot')
 from realistic_characters import improve
 return improve(groups,profile,PROFILES,BI)

def create_character(game,parent_movement_id=0,profile='Elias'):
 p=PROFILES[profile];visual=Node(profile+' model',game,layer=8 if parent_movement_id else 9,static=False);visual.scale=[p[-1]]*3
 positions={b[0]:np.array(b[2]) for b in BONES};bones={}
 for name,parent,pos in BONES:
  local=np.array(pos)-(positions[parent] if parent else np.zeros(3));bones[name]=Node(name,bones.get(parent,visual),local,layer=visual.layer,static=False)
 marker=profile+'_Body_'
 if not any(k.startswith(marker) for k in MESHES):
  for mat,mesh in build_body(profile).items():save_mesh(marker+mat[2:],mesh,'Characters/Population',bones=[b[2] for b in BONES])
 for name,(path,mesh) in list(MESHES.items()):
  if not name.startswith(marker):continue
  mat='M_'+name[len(marker):];n=Node(name,visual,layer=visual.layer,static=False);n.mesh=name;n.mat=mat;n.skinBones=[bones[b[0]].id for b in BONES]
  body=renderer_body(MATERIALS[mat])+f'  m_Quality: 4\n  m_UpdateWhenOffscreen: 0\n  m_SkinnedMotionVectors: 1\n  m_Mesh: {ref(path)}\n  m_Bones:\n'+''.join(f'  - {{fileID: {bones[b[0]].tid}}}\n' for b in BONES)+f'  m_BlendShapeWeights: []\n  m_RootBone: {{fileID: {bones["Hips"].tid}}}\n  m_AABB:\n    m_Center: {{x: 0, y: 0.9, z: 0}}\n    m_Extent: {{x: 1, y: 1.1, z: 0.7}}\n  m_DirtyAABB: 0\n'
  n.component(137,body)
 aid=visual.component(95,f'  m_Enabled: 1\n  m_Avatar: {{fileID: 0}}\n  m_Controller: {ref("Assets/_DesertShift/Animations/Character/AC_EliasCalder.controller",9100000)}\n  m_CullingMode: 0\n  m_UpdateMode: 0\n  m_ApplyRootMotion: 0\n  m_LinearVelocityBlending: 0\n  m_StabilizeFeet: 1\n  m_WarningMessage: \n  m_HasTransformHierarchy: 1\n  m_AllowConstantClipSamplingOptimization: 1\n  m_KeepAnimatorStateOnDisable: 0\n  m_WriteDefaultValuesOnDisable: 0\n')
 mapping='  humanBones:\n'+''.join(f'  - humanName: {n}\n    bone: {{fileID: {bones[n].tid}}}\n' for n,_,_ in BONES if n!='Root')
 visual.script('CharacterRig',mapping+f'  animator: {{fileID: {aid}}}\n')
 fields=f'  movement: {{fileID: {parent_movement_id}}}\n  animator: {{fileID: {aid}}}\n  skeleton:\n'+''.join(f'  - {{fileID: {bones[n].tid}}}\n' for n,_,_ in BONES)+'  strideScale: 1\n'
 visual.script('Assets/Game/Scripts/Actors/PrisonLocomotion.cs',fields)
 bones['LeftUpperArm'].rot=[0,0,82];bones['RightUpperArm'].rot=[0,0,-82]
 return visual,bones
