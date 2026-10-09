"""Hand-composed original Desert Shift set, authored as native scene objects."""
import math,random
import numpy as np
from geometry import *
from unity_writer import *

RNG=random.Random(8413);seq=0
def catalog():
    save_mesh('BevelBox',box(),'Props');save_mesh('SoftBox',box(bevel=.10),'Props')
    save_mesh('Cylinder',cylinder(.5,1,24),'Props');save_mesh('Sphere',ellipsoid((1,1,1),12,20),'Props')
    save_mesh('Plane',plane(),'Props')
    vertical=Mesh().merge(plane(),rot=(90,0,0));vertical.uv=[(1-u,v) for u,v in vertical.uv]
    save_mesh('Vertical',vertical,'Props')
    save_mesh('Tire',torus(.37,.13,40,14),'Environment/RV')
    save_mesh('HoseCoil',torus(.3,.025,36,8),'Props')
    save_mesh('Bottle',lathe([(0,.06),(.015,.075),(.20,.075),(.23,.034),(.30,.034),(.31,.03)],24),'Props')
    save_mesh('Beaker',lathe([(0,.1),(.012,.11),(.20,.115),(.21,.12),(.213,.11),(.018,.101),(0,.1)],28),'Props')
    save_mesh('Barrel',lathe([(-.45,.29),(-.42,.31),(-.34,.31),(-.33,.324),(-.3,.324),(-.29,.31),(.29,.31),(.30,.324),(.33,.324),(.34,.31),(.42,.31),(.45,.29)],32),'Props')
    save_mesh('Bucket',lathe([(0,.13),(.01,.14),(.28,.175),(.30,.182),(.31,.177),(.31,.164),(.04,.13)],24),'Props')
    for i in range(7):save_mesh(f'Rock_{i}',ellipsoid((1,1,1),9,16,seed=i+1),'Environment/Desert')
    for i in range(4):
        m=Mesh();rng=random.Random(201+i)
        for k in range(9):
            angle=k*2.4;h=rng.uniform(.18,.6);r=rng.uniform(.07,.2)
            base=(rng.uniform(-.1,.1),0,rng.uniform(-.1,.1));tip=(math.cos(angle)*r,h,math.sin(angle)*r)
            m.merge(tube([base,(tip[0]*.5,h*.6,tip[2]*.5),tip],.009,5))
            m.merge(ellipsoid((.18,.17,.18),5,7,seed=k+1),tip)
        save_mesh('Sage_'+str(i),m,'Environment/Desert')
    for i in range(3):
        m=Mesh();rng=random.Random(i+78)
        for k in range(15):
            a=k*2.4;h=rng.uniform(.18,.5);r=rng.uniform(.1,.34)
            p=(math.cos(a)*r,h*.75,math.sin(a)*r);width=.012
            m.quad((-width,0,0),(width,0,0),(p[0]+width,p[1],p[2]),(p[0]-width,p[1],p[2]))
            m.tri((p[0]-width,p[1],p[2]),(p[0]+width,p[1],p[2]),(p[0]*1.5,h,p[2]*1.5))
        save_mesh('Grass_'+str(i),m,'Environment/Desert')
    m=Mesh()
    for i in range(22):
        a=i*2.399;h=.4+(i%5)*.06;r=.35+(i%4)*.08
        left=np.array([math.cos(a+1.57)*.03,.06,math.sin(a+1.57)*.03]);mid=np.array([math.cos(a)*r*.5,h*.8,math.sin(a)*r*.5]);tip=np.array([math.cos(a)*r,h*.52,math.sin(a)*r])
        m.quad(-left,left,mid+left*.75,mid-left*.75);m.tri(mid-left*.75,mid+left*.75,tip)
    save_mesh('Yucca',m,'Environment/Desert')

def item(name,parent,pos,size,mat='M_Metal',mesh='BevelBox',rot=(0,0,0),coll=False,static=True):
    n=Node(name,parent,pos,rot,size,static=static).render(mesh,mat)
    if coll or name in ['Side window','Windshield','Rear window','Office window glazing']:n.boxcollider()
    return n
def pipe(parent,name,points,r=.025,mat='M_DarkMetal'):
    global seq;seq+=1;mn=f'Curve_{seq:04d}';save_mesh(mn,tube(points,r,8),'Props/Curves')
    return Node(name,parent).render(mn,mat)
def sign(parent,name,pos,size=(1,.5),rot=0):
    return item(name,parent,pos,(size[0],size[1],1),'M_Sign_'+name,'Vertical',(0,rot,0))
def surface(n,kind):n.script('SurfaceTag',f'  surface: {kind}\n');return n
def light(parent,name,pos,power=2,range_=6,color=(1,.85,.61),kind=2,rot=(0,0,0),shadows=0):
    n=Node(name,parent,pos,rot,static=False)
    cid=n.component(108,f'''  m_Enabled: 1
  serializedVersion: 11
  m_Type: {kind}
  m_Shape: 0
  m_Color: {col([*color,1])}
  m_Intensity: {power}
  m_Range: {range_}
  m_SpotAngle: 70
  m_InnerSpotAngle: 40
  m_CookieSize: 10
  m_Shadows:
    m_Type: {shadows}
    m_Resolution: 1
    m_CustomResolution: -1
    m_Strength: 0.85
    m_Bias: 0.035
    m_NormalBias: 0.3
    m_NearPlane: 0.1
    m_CullingMatrixOverride:
      e00: 1
      e01: 0
      e02: 0
      e03: 0
      e10: 0
      e11: 1
      e12: 0
      e13: 0
      e20: 0
      e21: 0
      e22: 1
      e23: 0
      e30: 0
      e31: 0
      e32: 0
      e33: 1
    m_UseCullingMatrixOverride: 0
  m_Cookie: {{fileID: 0}}
  m_DrawHalo: 0
  m_Flare: {{fileID: 0}}
  m_RenderMode: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingLayerMask: 1
  m_Lightmapping: 4
  m_LightShadowCasterMode: 0
  m_AreaSize: {{x: 1, y: 1}}
  m_BounceIntensity: 1
  m_ColorTemperature: 5500
  m_UseColorTemperature: 0
  m_BoundingSphereOverride: {{x: 0, y: 0, z: 0, w: 0}}
  m_UseBoundingSphereOverride: 0
  m_UseViewFrustumForShadowCasterCull: 1
  m_ShadowRadius: 0
  m_ShadowAngle: 0
''')
    return n,cid

def door(parent,name,pos,width=1.05,height=2.15,rot=0,mat='M_Turquoise',locked=False,window=True):
    n=Node(name,parent,pos,(0,rot,0),static=False)
    leaf=item('Door leaf',n,(width/2,height/2,0),(width,height,.07),mat,coll=True,static=False)
    leafid=next(cid for cls,cid,_ in leaf.parts if cls==65)
    for side in [-1,1]:
        item('Latch plate',n,(width-.11,height*.46,side*.044),(.09,.22,.02),'M_Chrome',static=False)
        item('Lever',n,(width-.16,height*.46,side*.082),(.16,.025,.025),'M_DarkMetal',static=False)
        if window:
            item('Inset panel',n,(width/2,height*.75,side*.04),(width*.62,height*.28,.012),'M_RV_Glass',static=False)
    for y in [.20,height-.20]:item('Hinge',n,(.016,y,0),(.025,.1,.09),'M_Chrome',static=False)
    cid=n.script('DoorController',f'  hinge: {{fileID: {n.tid}}}\n  leaf: {{fileID: {leafid}}}\n  doorName: {name}\n  locked: {int(locked)}\n  openAngle: 105\n  degreesPerSecond: 115\n  OpensPositiveByDefault: 1\n')
    return n,cid

def chair(parent,pos,rot=0,folding=False):
    n=Node('Folding chair' if folding else 'Chair',parent,pos,(0,rot,0));mat='M_ChairFabric' if folding else 'M_InteriorWood'
    item('Seat',n,(0,.43,0),(.49,.065,.44),mat,coll=True)
    item('Back',n,(0,.77,.21),(.49,.56,.055),mat,rot=(9,0,0),coll=True)
    for x in [-.20,.20]:
        for z in [-.18,.18]:item('Tubular leg',n,(x,.22,z),(.023,.46,.023),'M_Metal',rot=(z*30,0,-x*20))
        item('Armrest',n,(x,.65,0),(.04,.04,.45),'M_InteriorWood')
    return n
def table(parent,pos,size=(1.3,.73,.7),mat='M_InteriorWood'):
    n=Node('Work table',parent,pos);w,h,d=size;surface(item('Top',n,(0,h,0),(w,.07,d),mat,coll=True),3)
    for x in [-w*.42,w*.42]:
      for z in [-d*.4,d*.4]:item('Leg',n,(x,h*.5,z),(.045,h,.045),'M_Metal',coll=True)
    return n
def crate(parent,pos,size=(.6,.48,.45),mat='M_Wood',rot=0):
    n=Node('Storage crate',parent,pos,(0,rot,0));item('Crate',n,(0,size[1]/2,0),size,mat,coll=True)
    for x in [-size[0]*.38,size[0]*.38]:item('Band',n,(x,size[1]/2,0),(.032,size[1]+.008,size[2]+.012),'M_DarkMetal')
    item('Label',n,(0,size[1]*.65,-size[2]/2-.006),(.2,.1,.01),'M_Paper')
    return n
def barrel(parent,pos,mat='M_FadedRed'):
    n=item('Steel drum',parent,pos,(1,1,1),mat,'Barrel',coll=False);n.boxcollider((.65,.9,.65))
    for y in [-.42,.42]:item('Drum lid',n,(0,y,0),(.585,.022,.585),'M_DarkMetal','Cylinder')
    return n
def bottle(parent,pos,scale=1):return item('Sample vessel',parent,pos,(scale,scale,scale),'M_BlueGlass','Bottle')
def shelf(parent,pos,w=1.5,h=1.9,d=.45):
    n=Node('Storage shelving',parent,pos)
    for x in [-w/2,w/2]:
      for z in [-d/2,d/2]:item('Upright',n,(x,h/2,z),(.045,h,.045),'M_DarkMetal',coll=True)
    for y in [.12,.62,1.12,1.70]:item('Shelf',n,(0,y,0),(w,.035,d),'M_Metal',coll=True)
    return n

def make_rv(env):
    x,z=-77,-18;y=float(terrain_height(x,z))+.06
    camp=Node('RV_Area',env,(x,y,z),(0,-18,0));rv=Node('Sundowner_84_RV',camp)
    # 8.6 x 2.5 x 3.2m. Wall segmentation leaves real door and window openings.
    surface(item('Timber floor',rv,(0,.55,0),(2.44,.16,8.35),'M_InteriorWood',coll=True),3)
    item('Chassis',rv,(0,.31,0),(2.1,.27,7.95),'M_DarkMetal')
    item('Roof crown',rv,(0,3.08,0),(2.5,.20,8.5),'M_RV_Upper',mesh='SoftBox',coll=True)
    # Rear wall with a high window opening.
    item('Rear lower',rv,(0,1.16,-4.18),(2.5,1.18,.10),'M_RV_Body',coll=True)
    item('Rear upper',rv,(0,2.86,-4.18),(2.5,.31,.10),'M_RV_Upper',coll=True)
    for sx in [-1,1]:item('Rear pillar',rv,(sx*.965,2.23,-4.18),(.55,1.01,.10),'M_RV_Upper',coll=True)
    item('Rear window',rv,(0,2.25,-4.19),(1.37,.78,.02),'M_RV_Glass')
    # Side sections, subdivided at every opening to keep the interior enterable.
    for sx in [-1,1]:
        # Side door on right at z +1.3..+2.45. The remaining side sill is uninterrupted.
        spans=[(-4.15,1.3),(2.45,4.10)] if sx==1 else [(-4.15,4.10)]
        for za,zb in spans:
            item('Lower side',rv,(sx*1.20,1.24,(za+zb)/2),(.11,1.26,zb-za),'M_RV_Body',coll=True)
            item('Orange beltline',rv,(sx*1.262,1.19,(za+zb)/2),(.012,.22,zb-za),'M_RV_Stripe')
            item('Brown pinstripe',rv,(sx*1.27,1.02,(za+zb)/2),(.009,.05,zb-za),'M_RV_StripeDark')
        item('Upper side strip',rv,(sx*1.2,2.875,-.025),(.11,.24,8.25),'M_RV_Upper',coll=True)
        windows=[(-3.5,-2.20),(-1.68,-.20),(.25,1.0),(2.60,3.83)] if sx==1 else [(-3.5,-2.10),(-1.5,.20),(.80,2.15),(2.7,3.83)]
        gaps=[];last=-4.15
        for a,b in windows:
            if a>last:gaps.append((last,a))
            item('Side window',rv,(sx*1.215,2.30,(a+b)/2),(.025,.85,b-a),'M_RV_Glass')
            for yy in [1.86,2.74]:item('Window seal',rv,(sx*1.272,yy,(a+b)/2),(.05,.04,b-a+.08),'M_RV_Rubber')
            for zz in [a,b]:item('Window frame',rv,(sx*1.273,2.30,zz),(.05,.90,.04),'M_RV_Rubber')
            # Small interior curtains frame the warm incoming light.
            for zz in [a+.07,b-.07]:item('Curtain',rv,(sx*1.13,2.29,zz),(.04,.88,.14),'M_ChairFabric')
            last=b
        gaps.append((last,4.10))
        for a,b in gaps:
            if sx==1 and a<2.45 and b>1.3:
                if a<1.3:item('Door pillar',rv,(sx*1.2,2.30,(a+1.3)/2),(.11,.86,1.3-a),'M_RV_Upper',coll=True)
                if b>2.45:item('Door pillar',rv,(sx*1.2,2.30,(2.45+b)/2),(.11,.86,b-2.45),'M_RV_Upper',coll=True)
            else:item('Side pillar',rv,(sx*1.2,2.30,(a+b)/2),(.11,.86,b-a),'M_RV_Upper',coll=True)
    # Original upright cab: full windscreen, split glazing, front grille and bumper.
    item('Front fascia',rv,(0,1.10,4.10),(2.48,1.08,.22),'M_RV_Body',mesh='SoftBox',coll=True)
    item('Cab brow',rv,(0,2.82,4.07),(2.48,.34,.20),'M_RV_Upper',mesh='SoftBox',coll=True)
    for sx in [-1,1]:
        item('Cab pillar',rv,(sx*1.17,2.17,4.11),(.15,1.04,.15),'M_RV_Upper',coll=True)
        item('Windshield',rv,(sx*.58,2.18,4.11),(1.03,1.03,.018),'M_RV_Glass',rot=(-7,0,0))
        pipe(rv,'Windshield wiper',[(sx*.55,1.72,4.18),(sx*.48,2.00,4.18),(sx*.76,2.15,4.18)],.017,'M_RV_Rubber')
        pipe(rv,'Mirror arm',[(sx*1.23,1.78,3.76),(sx*1.62,1.89,3.9),(sx*1.62,2.12,3.9)],.025,'M_Chrome')
        item('Mirror body',rv,(sx*1.64,2.20,3.90),(.20,.38,.10),'M_RV_Rubber',mesh='SoftBox')
        item('Mirror glass',rv,(sx*1.64,2.20,3.96),(.17,.33,.011),'M_Chrome')
        item('Headlight surround',rv,(sx*.91,1.02,4.25),(.45,.32,.045),'M_DarkMetal')
        for xx in [sx*.78,sx*1.035]:item('Headlight',rv,(xx,1.03,4.287),(.195,.23,.06),'M_Light',mesh='SoftBox')
        item('Rear taillight',rv,(sx*.98,1.0,-4.25),(.16,.40,.06),'M_RedLight')
        item('Amber running light',rv,(sx*.82,2.99,4.17),(.15,.07,.04),'M_PlasticOrange')
    item('Windscreen center seal',rv,(0,2.19,4.17),(.045,1.1,.03),'M_RV_Rubber')
    for y in [.84,.90,.96,1.02,1.08,1.14]:item('Grille louvre',rv,(0,y,4.255),(1.03,.025,.03),'M_DarkMetal')
    for z in [-4.36,4.34]:item('Bumper',rv,(0,.57,z),(2.57,.22,.20),'M_Chrome',mesh='SoftBox',coll=True)
    sign(rv,'RV_BADGE',(0,1.43,4.227),(.72,.30));sign(rv,'LICENSE',(0,.78,-4.32),(.44,.22),180)
    sign(rv,'LICENSE',(0,.57,4.45),(.44,.22))
    for z in [-2.62,2.66]:
        for sx in [-1,1]:
            wheel=item('All terrain tire',rv,(sx*1.18,.53,z),(1,1,1),'M_RV_Rubber','Tire',(0,0,90));wheel.boxcollider((1,.30,1))
            item('Steel hub',rv,(sx*1.335,.53,z),(.45,.10,.45),'M_Chrome','Cylinder',(0,0,90))
            for j in range(8):
                a=j*math.tau/8;item('Wheel bolt',rv,(sx*1.39,.53+math.cos(a)*.145,z+math.sin(a)*.145),(.025,.026,.025),'M_DarkMetal','Sphere')
            # Separate thick arch trim, with the wheel exposed below the sill.
            pts=[(sx*1.284,.52+math.sin(a)*.57,z+math.cos(a)*.57) for a in np.linspace(0,math.pi,25)]
            pipe(rv,'Wheel arch lip',pts,.055,'M_RV_Rubber')
    for z in [-1.9,.4,2.9]:
        item('Roof vent pedestal',rv,(0,3.21,z),(.7,.11,.7),'M_DarkMetal')
        item('Roof vent hood',rv,(0,3.29,z),(.78,.09,.78),'M_RV_Upper',mesh='SoftBox')
    pipe(rv,'Exhaust',[(.6,.25,-3.5),(.8,.22,-4.15),(1.25,.22,-4.2)],.052,'M_DarkMetal')
    # Door hinge local +X runs toward rear of RV, real opening 1.15m wide.
    dn,dc=door(rv,'RV side door',(1.27,.63,2.45),1.15,2.13,90,'M_RV_Upper')
    rv.script('RVController',f'  sideDoor: {{fileID: {dc}}}\n  vehicleName: Sundowner 84\n')
    for i in range(3):surface(item('Entry step',rv,(1.45+(2-i)*.28,.10+i*.18,1.875),(.45,.18,1.15),'M_DarkMetal',coll=True),2)
    # Two genuine cab seats and dashboard.
    for sx in [-1,1]:
        seat=chair(rv,(sx*.62,.64,3.03),180);seat.name='Driver seat' if sx==-1 else 'Passenger seat'
    item('Dashboard',rv,(0,1.35,3.82),(2.20,.23,.46),'M_RV_StripeDark',mesh='SoftBox',coll=True)
    item('Instrument pod',rv,(-.62,1.52,3.70),(.55,.17,.26),'M_DarkMetal')
    for xx in [-.76,-.57]:item('Gauge',rv,(xx,1.53,3.552),(.12,.12,.014),'M_EyeWhite','Cylinder',(90,0,0))
    item('Steering column',rv,(-.61,1.23,3.33),(.06,.6,.06),'M_DarkMetal','Cylinder',(40,0,0))
    item('Steering wheel',rv,(-.61,1.49,3.24),(.57,.57,.57),'M_RV_Rubber','HoseCoil',(48,0,0))
    # Kitchen along left, clear centre aisle and upholstered rear dinette.
    item('Kitchen base',rv,(-.87,1.04,.25),(.53,.83,2.5),'M_InteriorWood',coll=True)
    surface(item('Countertop',rv,(-.86,1.48,.25),(.66,.055,2.62),'M_Paper',coll=True),3)
    item('Sink rim',rv,(-.86,1.518,.85),(.44,.021,.52),'M_Chrome')
    item('Sink inset',rv,(-.86,1.53,.85),(.36,.01,.43),'M_DarkMetal')
    pipe(rv,'Faucet',[(-1.01,1.51,.88),(-1.01,1.80,.88),(-.82,1.82,.88),(-.77,1.73,.88)],.018,'M_Chrome')
    for zz in [-.55,.12,.80]:
        door(rv,'kitchen cabinet',(-.59,.66,zz+.29),.58,.69,90,'M_InteriorWood',window=False)
    for sx in [-1,1]:
        item('Overhead storage',rv,(sx*.90,2.76,-.9),(.45,.36,3.9),'M_InteriorWood',coll=True)
        item('Rear bench',rv,(sx*.80,.91,-2.78),(.61,.56,1.70),'M_ChairFabric',mesh='SoftBox',coll=True)
        item('Rear bench back',rv,(sx*1.075,1.37,-2.78),(.08,.56,1.7),'M_ChairFabric',mesh='SoftBox',coll=True)
    table(rv,(0,.62,-2.85),(.83,.74,1.37));sign(rv,'NOTEBOOK',(.05,1.410,-2.88),(.27,.17),0).rot=[-90,0,0]
    for zz in [-.47,-.05,.32]:bottle(rv,(-.83,1.518,zz),.75)
    item('Beaker',rv,(-.73,1.52,-.68),(.6,.7,.6),'M_BlueGlass','Beaker')
    item('Measurement instrument',rv,(-.85,1.60,-.35),(.25,.14,.19),'M_Plastic')
    item('Instrument screen',rv,(-.56,1.63,-.35),(.012,.07,.13),'M_Iris')
    crate(rv,(.77,.64,-1.23),(.56,.55,.67),'M_Plastic')
    crate(rv,(.78,.64,-3.63),(.55,.53,.65),'M_Wood')
    for zz in [-.7,2.2]:
        item('Ceiling fixture',rv,(0,2.95,zz),(.27,.045,.55),'M_Light');light(rv,'Warm interior lamp',(0,2.78,zz),1.4,4)
    # Dust and rust accents are shallow geometry and share the existing material set.
    for i in range(20):
        zz=RNG.uniform(-4,4);sx=RNG.choice([-1,1]);
        if sx==1 and 1.3<zz<2.45:continue
        item('Sun weathering',rv,(sx*1.274,RNG.uniform(.68,.98),zz),(.008,RNG.uniform(.012,.05),RNG.uniform(.04,.19)),'M_RV_StripeDark')
    # Composed camp arrangement: chairs facing the mountain opening, gear under awning side.
    chair(camp,(4,0,-.8),-25,True);chair(camp,(5.8,0,-1.4),30,True)
    camp_table=table(camp,(4.95,0,-.35),(1.15,.73,.63),'M_Paper')
    item('Field radio',camp_table,(.18,.9,0),(.34,.24,.16),'M_Plastic')
    pipe(camp_table,'Radio antenna',[(.28,1.0,0),(.38,1.48,0)],.006,'M_Chrome')
    item('Cooler',camp,(3.1,.23,-2.1),(.8,.46,.44),'M_Turquoise',mesh='SoftBox',coll=True)
    item('Cooler lid',camp,(3.1,.49,-2.1),(.82,.07,.46),'M_Paper')
    item('Toolbox',camp,(4.4,.15,.85),(.55,.30,.28),'M_FadedRed',coll=True)
    item('Toolbox grip',camp,(4.4,.34,.85),(.23,.05,.03),'M_RV_Rubber')
    for i in range(2):
        item('Water canister',camp,(2.8+i*.49,.29,-3.6),(.36,.58,.28),'M_Plastic',mesh='SoftBox',coll=True)
        item('Water lid',camp,(2.8+i*.49,.6,-3.6),(.08,.04,.08),'M_RV_Rubber','Cylinder')
    crate(camp,(3.7,0,-3.5));crate(camp,(3.8,.48,-3.5),(.51,.33,.40),'M_Paper',7)
    barrel(camp,(-2.3,.46,-3.7));barrel(camp,(-3,.46,-3.25),'M_Turquoise')
    item('Spare tire',camp,(-2.05,.51,-1.8),(1,1,1),'M_RV_Rubber','Tire',(0,0,18))
    item('Cable spool',camp,(-2.8,.38,-.6),(.69,.59,.69),'M_Wood','Cylinder',coll=True)
    for yy in [.11,.66]:item('Spool flange',camp,(-2.8,yy,-.6),(.9,.08,.9),'M_InteriorWood','Cylinder')
    gen=Node('Portable generator',camp,(3.7,0,-5.4));item('Engine',gen,(0,.33,0),(.6,.51,.4),'M_FadedRed',coll=True)
    for xx in [-.36,.36]:pipe(gen,'Generator cage',[(xx,.05,-.3),(xx,.68,-.3),(xx,.68,.3),(xx,.05,.3)],.022,'M_DarkMetal')
    pipe(camp,'Power lead',[(3.7,.035,-5.2),(3,.03,-4.7),(1.5,.035,-4.5),(.8,.2,-4.0)],.014,'M_RV_Rubber')
    for p in [(-2.0,.22,-4.8),(-2.6,.19,-4.6)]:item('Refuse sack',camp,p,(.43,.42,.43),'M_RV_Rubber','Sphere',rot=(10,30,5))
    for p in [(4.65,.84,-.35),(5.20,.84,-.29)]:item('Fictional soda can',camp,p,(.075,.14,.075),'M_FadedRed','Cylinder')
    item('Lantern base',camp,(4.8,.80,-.35),(.14,.06,.14),'M_DarkMetal','Cylinder')
    item('Lantern glass',camp,(4.8,.94,-.35),(.09,.21,.09),'M_Light','Cylinder')
    camp.script('EnvironmentAudio',f'  clip: {ref("Assets/_DesertShift/Audio/Generator.wav",8300000,3)}\n  volume: 0.11\n  spatial: 1\n  range: 19\n')
    save_prefab(rv,'Environment','PF_Sundowner84_RV')
    save_prefab(camp_table,'Props','PF_CampTable');save_prefab(dn,'Interactables','PF_RVDoor')
    return camp,rv

def make_carwash(env):
    x,z=89,-12;base=float(terrain_height(x,z))+.08
    root=Node('Sunset_Splash_CarWash',env,(x,base,z));yard=Node('Parking and service yard',root)
    surface(item('Parking asphalt',yard,(1,-.045,-12),(55,.12,46),'M_Asphalt',coll=True),5)
    # Three 5.6m wide through bays, plus a side office block.
    building=Node('Three bay building',root)
    surface(item('Main slab',building,(0,.03,0),(19.4,.16,14),'M_Concrete',coll=True),1)
    for xx in [-9.4,-3.15,3.15,9.4]:
        item('Stucco pier wall',building,(xx,2.0,0),(.32,4,14),'M_CarWashStucco',coll=True)
        item('Turquoise base trim',building,(xx,.38,-.03),(.35,.63,14),'M_Turquoise')
        item('Bay front column cap',building,(xx,3.98,-7),(.60,.16,.55),'M_Turquoise')
    item('Main roof',building,(0,4.08,0),(19.6,.25,14.3),'M_CarWashStucco',coll=True)
    for zz in [-7.14,7.14]:
        item('Turquoise fascia',building,(0,4.10,zz),(19.7,.46,.16),'M_Turquoise',coll=True)
        item('Terracotta lip',building,(0,4.36,zz),(19.8,.09,.25),'M_FadedRed')
    sign(building,'SUNSET_SPLASH',(0,5.23,-7.24),(7.8,2.08),180)
    # Sign backing and braces.
    item('Main sign backing',building,(0,5.23,-7.12),(8.1,2.30,.16),'M_Turquoise',coll=True)
    for xx in [-3.2,3.2]:item('Sign support',building,(xx,4.82,-6.85),(.12,1.6,.12),'M_DarkMetal')
    bay_lights=[]
    for bay,xx in enumerate([-6.3,0,6.3],1):
        n=Node('Wash bay '+str(bay),building,(xx,0,0))
        surface(item('Damp concrete',n,(0,.12,0),(5.75,.025,13.5),'M_WetConcrete',coll=True),4)
        for zz in [-3.8,2.0,4.8]:
            item('Puddle',n,(RNG.uniform(-1.5,1.5),.139,zz),(RNG.uniform(.8,2.3),.004,RNG.uniform(.7,2.4)),'M_Puddle','Sphere')
        for i in range(12):
            item('Soap residue',n,(RNG.uniform(-1.8,1.8),.143,RNG.uniform(-5,5)),(RNG.uniform(.03,.11),.005,RNG.uniform(.02,.12)),'M_Foam','Sphere')
        item('Drain channel',n,(0,.132,0),(.40,.018,11),'M_DarkMetal')
        for zz in np.arange(-5.4,5.4,.23):item('Drain grate',n,(0,.15,float(zz)),(.37,.02,.027),'M_Metal')
        item('Control cabinet',n,(-2.75,1.56,-3.8),(.26,.72,.58),'M_Turquoise',coll=True)
        item('Control face',n,(-2.60,1.60,-3.80),(.015,.41,.41),'M_Paper')
        for zz in [-3.95,-3.8,-3.65]:item('Selector button',n,(-2.58,1.57,zz),(.04,.055,.055),'M_PlasticOrange','Sphere')
        pipe(n,'High pressure supply',[(-2.86,.3,4),(-2.86,3.3,4),(-2.86,3.3,-3.8),(-2.86,1.90,-3.8)],.04,'M_Chrome')
        pipe(n,'Overhead boom',[(-2.88,3.70,1.2),(-1,3.70,1.2),(0,3.55,1.2)],.055,'M_DarkMetal')
        hose=[(0,3.48,1.2),(.10,2.7,1.30),(.30,1.90,1.48),(.44,.85,1.2),(.35,.55,.6),(.03,.70,.2),(-.2,1.4,.2)]
        pipe(n,'Hanging hose',hose,.030,'M_RV_Rubber')
        item('Pressure spray grip',n,(-.2,1.40,.20),(.09,.27,.045),'M_Plastic',rot=(0,0,-20))
        pipe(n,'Spray lance',[(-.2,1.55,.2),(-.2,1.68,-.37),(-.2,1.75,-.65)],.014,'M_Chrome')
        item('Foam brush handle',n,(2.68,1.10,-1.1),(.035,1.7,.035),'M_Chrome','Cylinder',rot=(0,0,8))
        item('Brush head',n,(2.56,.23,-1.1),(.28,.13,.15),'M_Turquoise')
        item('Brush bristles',n,(2.56,.15,-1.1),(.25,.09,.13),'M_Grass')
        for zz in [-4.8,4.8]:item('Bucket',n,(2.30,.14,zz),(1,1,1),'M_PlasticOrange','Bucket')
        for j in range(2):bottle(n,(2.38,.14,3.6+j*.28),1.2)
        # Warning plaque sits on side wall, readable from inside the bay.
        sign(n,'BAY_RULES',(-2.97,2.2,-.5),(1.20,.6),90)
        for zz in [-3,3]:
            item('Fluorescent fixture',n,(0,3.89,zz),(.23,.09,1.35),'M_DarkMetal')
            item('Fluorescent tube',n,(0,3.82,zz),(.13,.04,1.22),'M_Light')
            _,lc=light(n,'Bay work light',(0,3.65,zz),1.45,7,(.78,.91,1));bay_lights.append(lc)
    # Office block x 10..19, z -7..+7; internal partitions leave 1.2m passages.
    annex=Node('Office and staff rooms',root)
    surface(item('Annex floor',annex,(14.4,.045,0),(9.7,.17,14),'M_Concrete',coll=True),1)
    item('Annex roof',annex,(14.4,3.32,0),(9.7,.24,14.3),'M_CarWashStucco',coll=True)
    item('Roof terrace curb south',annex,(19.25,3.59,-4.2),(.25,.45,5.9),'M_Turquoise',coll=True)
    item('Roof terrace curb north',annex,(19.25,3.59,3.8),(.25,.45,6.7),'M_Turquoise',coll=True)
    item('Right exterior wall',annex,(19.15,1.64,0),(.24,3.28,14),'M_CarWashStucco',coll=True)
    item('Rear exterior wall',annex,(14.4,1.64,6.9),(9.7,3.28,.22),'M_CarWashStucco',coll=True)
    # Front office entrance at x 12.5..13.7, windows x 14.1..18.3.
    for xx,ww in [(10.97,2.87),(13.9,.35),(18.72,.95)]:item('Office frontage',annex,(xx,1.64,-6.9),(ww,3.28,.20),'M_CarWashStucco',coll=True)
    item('Office window sill',annex,(16.2,.64,-6.9),(4.25,1.23,.20),'M_CarWashStucco',coll=True)
    item('Office window header',annex,(16.2,2.92,-6.9),(4.25,.72,.20),'M_CarWashStucco',coll=True)
    item('Office window glazing',annex,(16.2,1.92,-6.93),(4.23,1.26,.03),'M_RV_Glass')
    for xx in [14.1,16.2,18.3]:item('Office window frame',annex,(xx,1.92,-6.96),(.065,1.33,.065),'M_Turquoise')
    item('Office door lintel',annex,(13.05,2.83,-6.9),(1.34,.90,.20),'M_CarWashStucco',coll=True)
    od,oc=door(annex,'office door',(13.72,.14,-6.96),1.25,2.22,180)
    sign(annex,'OFFICE',(13.1,2.98,-7.025),(1.34,.40),180)
    # Cross corridor z -.5..+1.2; four back rooms open into corridor.
    for xx,ww in [(11.04,2.93),(16.37,5.46)]:item('Office rear partition',annex,(xx,1.65,-.55),(ww,3.18,.13),'M_CarWashStucco',coll=True)
    door(annex,'office corridor door',(12.5,.14,-.55),1.14,2.18,0,'M_InteriorWood')
    item('Corridor lintel',annex,(13.05,2.83,-.55),(1.2,.8,.15),'M_CarWashStucco',coll=True)
    # Back rooms: staff x10..14.1, storage14.1..19.1. Restroom/utility separated in back half.
    item('Rear central partition',annex,(14.08,1.65,4.0),(.14,3.18,5.8),'M_CarWashStucco',coll=True)
    for xx,ww in [(10.3,1.3),(13.15,1.85),(14.8,1.3),(18.0,2.30)]:item('Room front wall',annex,(xx,1.65,1.15),(ww,3.18,.14),'M_CarWashStucco',coll=True)
    for nm,xx in [('staff room door',11.0),('storage door',15.5)]:
        door(annex,nm,(xx,.14,1.13),1.16,2.18,0,'M_InteriorWood')
        item('Room door lintel',annex,(xx+.58,2.82,1.15),(1.18,.8,.14),'M_CarWashStucco',coll=True)
    sign(annex,'STAFF',(11.58,2.62,1.06),(1.03,.27),180)
    sign(annex,'STORAGE',(16.08,2.62,1.06),(1.03,.27),180)
    for xx,ww in [(10.16,1.14),(13.17,1.70),(14.7,1.05),(17.95,2.37)]:item('Rear room divider',annex,(xx,1.65,4.05),(ww,3.18,.14),'M_CarWashStucco',coll=True)
    for nm,xx,sg in [('restroom door',10.75,'RESTROOM'),('utility room door',15.3,'UTILITY')]:
        door(annex,nm,(xx,.14,4.05),1.16,2.18,0,'M_InteriorWood',window=False)
        item('Back lintel',annex,(xx+.58,2.82,4.05),(1.18,.8,.14),'M_CarWashStucco',coll=True)
        sign(annex,sg,(xx+.58,2.62,3.95),(1.06,.27),180)
    # Believable working office.
    table(annex,(16.0,.13,-4.60),(2.55,.78,.76),'M_InteriorWood')
    item('Computer base',annex,(15.5,.95,-4.5),(.42,.035,.27),'M_DarkMetal')
    item('Monitor stalk',annex,(15.5,1.10,-4.47),(.055,.3,.05),'M_DarkMetal')
    item('Computer display',annex,(15.5,1.34,-4.43),(.65,.42,.07),'M_DarkMetal')
    sign(annex,'MONITOR',(15.5,1.34,-4.477),(.57,.34),180)
    item('Keyboard',annex,(15.5,.98,-4.8),(.47,.025,.15),'M_Plastic')
    for xx in np.linspace(15.31,15.68,10):
        for zz in [-4.84,-4.80,-4.76]:item('Key',annex,(float(xx),1.002,zz),(.026,.005,.024),'M_Paper')
    chair(annex,(15.5,.14,-3.40),0)
    item('Cash register',annex,(16.72,1.06,-4.60),(.44,.28,.37),'M_Paper',mesh='SoftBox')
    item('Register display',annex,(16.72,1.27,-4.58),(.23,.11,.035),'M_DarkMetal')
    item('Telephone',annex,(17.02,.98,-4.76),(.22,.09,.18),'M_DarkMetal',mesh='SoftBox')
    item('Filing cabinet',annex,(18.55,.82,-1.33),(.74,1.36,.66),'M_Plastic',coll=True)
    for yy in [.35,.72,1.09]:
        item('Drawer front',annex,(18.55,yy,-1.68),(.66,.32,.032),'M_Turquoise');item('Drawer pull',annex,(18.55,yy,-1.72),(.17,.027,.04),'M_Chrome')
    item('Corkboard',annex,(18.995,1.95,-3.0),(.07,1.0,1.70),'M_Wood')
    for i in range(7):item('Paperwork',annex,(18.94,1.64+(i%3)*.27,-3.52+(i//3)*.44),(.015,.23,.3),'M_Paper',rot=(RNG.uniform(-9,9),0,0))
    for i in range(3):item('Desk paperwork',annex,(16.17,.960+i*.006,-4.51),(.22,.006,.31),'M_Paper',rot=(0,i*11,0))
    sign(annex,'NOTEBOOK',(16.3,.98,-4.48),(.21,.30)).rot=[-90,0,0]
    item('Clock case',annex,(17.15,2.60,-.655),(.50,.065,.50),'M_DarkMetal','Cylinder',(90,0,0))
    item('Clock face',annex,(17.15,2.60,-.701),(.44,.012,.44),'M_Paper','Cylinder',(90,0,0))
    item('Hour hand',annex,(17.13,2.65,-.714),(.02,.13,.01),'M_DarkMetal',rot=(0,0,20))
    item('Minute hand',annex,(17.23,2.60,-.714),(.17,.016,.01),'M_DarkMetal')
    fan=Node('Desk fan',annex,(17.05,.98,-4.37))
    item('Fan base',fan,(0,.01,0),(.22,.04,.18),'M_Plastic')
    item('Fan column',fan,(0,.20,0),(.035,.38,.04),'M_DarkMetal')
    item('Fan cage',fan,(0,.38,0),(.62,.62,.62),'M_Metal','HoseCoil',(90,0,0))
    for a in [0,120,240]:item('Fan blade',fan,(0,.38,0),(.29,.05,.03),'M_Plastic',rot=(0,0,a))
    # Staff kitchenette / break table.
    table(annex,(12.25,.14,2.75),(1.2,.75,.65));chair(annex,(12.2,.14,1.82),0);chair(annex,(12.2,.14,3.56),180)
    item('Staff fridge',annex,(10.12,1.01,3.02),(.70,1.75,.69),'M_Paper',mesh='SoftBox',coll=True)
    item('Fridge handle',annex,(10.36,1.22,2.65),(.027,.5,.05),'M_Chrome')
    # Storage keeps a navigable centre aisle and provides future hiding places.
    for xx in [14.55,18.55]:
        sh=shelf(annex,(xx,.15,2.65),.62,1.95,2.5)
        for j in range(4):crate(sh,(0,.14+(j%2)*.5,-.78+(j//2)*1.05),(.47,.35,.5),'M_Paper')
    for p in [(17.0,.15,3.55),(17.6,.15,3.55)]:item('Cleaning bucket',annex,p,(1,1,1),'M_Turquoise','Bucket')
    item('Spare hose',annex,(18.97,1.55,2.8),(1.4,1.4,1.4),'M_RV_Rubber','HoseCoil',(0,0,90))
    # Restroom: washbasin, mirror, cistern, bowl; utility: boiler, panel and pipes.
    item('Washbasin pedestal',annex,(10.17,.54,5.32),(.25,.78,.25),'M_Paper','Cylinder',coll=True)
    item('Washbasin',annex,(10.2,.96,5.32),(.58,.18,.43),'M_Paper',mesh='SoftBox')
    item('Mirror',annex,(9.68,1.73,5.32),(.03,.75,.61),'M_Chrome')
    item('Toilet base',annex,(12.55,.41,6.08),(.4,.56,.61),'M_Paper','Sphere',coll=True)
    item('Toilet tank',annex,(12.55,.9,6.47),(.52,.60,.2),'M_Paper',mesh='SoftBox',coll=True)
    item('Toilet seat',annex,(12.55,.70,6.02),(.58,.11,.66),'M_Paper','Tire')
    item('Boiler',annex,(18.23,1.30,5.85),(1.08,2.3,1.08),'M_Metal','Cylinder',coll=True)
    item('Electrical panel',annex,(14.25,1.5,5.40),(.13,1.18,.70),'M_DarkMetal',coll=True)
    for zz in [5.2,5.5,5.8]:pipe(annex,'Utility plumbing',[(14.32,.4,zz),(14.32,2.8,zz),(18.2,2.8,zz),(18.2,2.2,zz)],.025,'M_Metal')
    crate(annex,(15.0,.15,6.32),(.72,.65,.60),'M_Wood')
    # Office and back room fixtures.
    for xx,zz in [(15.5,-3),(12.2,2.7),(16.6,2.7),(12.2,5.6),(16.6,5.6)]:
        item('Ceiling tube',annex,(xx,3.14,zz),(1.05,.045,.12),'M_Light')
        light(annex,'Room light',(xx,2.92,zz),1.7,5,(.91,.90,.73))
    switch=item('Bay lighting switch',annex,(12.25,1.45,-6.76),(.13,.22,.08),'M_DarkMetal',coll=True,static=False)
    switch.script('LightSwitch','  controlledLights:\n'+''.join(f'  - {{fileID: {l}}}\n' for l in bay_lights)+'  switchName: wash bay lights\n')
    # Exterior stairs: no ladder teleport; walkable .18m risers and intermediate platform.
    stairs=Node('Roof access staircase',root,(21.3,0,0))
    for i in range(18):surface(item('Stair tread '+str(i+1),stairs,(0,.15+i*.18,-5.5+i*.28),(1.65,.17,.29),'M_DarkMetal',coll=True),2)
    surface(item('Roof landing',stairs,(-.85,3.31,-.46),(3.40,.14,1.75),'M_DarkMetal',coll=True),2)
    for xx in [-.87,.87]:
        pipe(stairs,'Stair handrail',[(xx,1.05,-5.55),(xx,4.14,-.60)],.035,'M_Chrome')
        for j in [0,4,8,12,17]:item('Baluster',stairs,(xx,.63+j*.18,-5.5+j*.28),(.035,1.0,.035),'M_Metal')
    # Roof curb leaves a proper opening at the stair landing.
    item('Roof access bridge',root,(19.50,3.32,-.40),(1.2,.17,1.65),'M_DarkMetal',coll=True)
    # Short second staircase to the bay roof.
    for i in range(5):item('Upper roof step',root,(9.95+i*.3,3.41+(4-i)*.16,2.8),(.3,.16,1.15),'M_DarkMetal',coll=True)
    for xx,zz in [(0,2.5),(-6.1,2.5),(16.6,3.4)]:
        item('Rooftop AC',root,(xx,4.55 if xx<10 else 3.78,zz),(1.65,.7,1.0),'M_Metal',coll=True)
        for j in range(8):item('AC louvre',root,(xx-.6+j*.16,4.91 if xx<10 else 4.14,zz),(.07,.025,.7),'M_DarkMetal')
    # Parking lines, wheel stops, roadside sign and vending machine.
    for i in range(6):
        xx=-13.5+i*3.2
        for edge in [-1,1]:item('Faded parking line',yard,(xx+edge*1.5,.024,-22),(.075,.01,5.5),'M_WhitePaint')
        item('Wheel stop',yard,(xx,.12,-19.35),(1.8,.22,.24),'M_Concrete',coll=True)
    signroot=Node('Roadside pylon sign',root,(-15,0,-21))
    for sx in [-1,1]:item('Sign post',signroot,(sx*1.8,2.8,0),(.15,5.6,.15),'M_DarkMetal',coll=True)
    item('Pylon backing',signroot,(0,5.0,0),(5.5,2.4,.23),'M_Turquoise')
    sign(signroot,'SUNSET_SPLASH',(0,5,-.13),(5.2,2.10),180)
    vend=Node('Cool Canyon vending machine',root,(18.6,.12,-8.2))
    item('Vending cabinet',vend,(0,.99,0),(.95,1.98,.7),'M_FadedRed',mesh='SoftBox',coll=True)
    sign(vend,'VENDING',(0,1.08,-.36),(.82,1.45),180)
    item('Vending dispenser',vend,(0,.25,-.365),(.65,.14,.03),'M_DarkMetal')
    item('Waste bin',root,(20.55,.65,-8.1),(.69,1.1,.69),'M_Turquoise',mesh='SoftBox',coll=True)
    bench=Node('Visitor bench',root,(14.9,.14,-8.4))
    for zz in [-.18,0,.18]:item('Bench slat',bench,(0,.43,zz),(1.95,.06,.14),'M_Wood',coll=True)
    for xx in [-.74,.74]:item('Bench support',bench,(xx,.2,0),(.08,.43,.48),'M_DarkMetal',coll=True)
    item('Bench back',bench,(0,.78,.24),(1.95,.39,.05),'M_Wood',coll=True)
    # Back service alley, chain mesh fencing and a dumpster.
    dumpster=Node('Service dumpster',root,(-12.7,0,8.9))
    item('Dumpster body',dumpster,(0,.72,0),(2.25,1.4,1.35),'M_Turquoise',mesh='SoftBox',coll=True)
    item('Dumpster lid',dumpster,(0,1.47,0),(2.34,.14,1.42),'M_DarkMetal',rot=(-4,0,0))
    for xx in [-.95,.95]:
      for zz in [-.5,.5]:item('Dumpster caster',dumpster,(xx,.13,zz),(.15,.2,.15),'M_RV_Rubber','Sphere')
    for i in range(5):crate(root,(-9.5+i*.79,.13,10.8),(.63,.65,.70),'M_Paper',RNG.uniform(-5,5))
    crate(root,(-8.6,.79,10.8),(.63,.44,.6),'M_Wood',15)
    for i in range(4):barrel(root,(14.8+i*.8,.46,10.4),'M_Turquoise')
    fence(root,(-16,0,13),(23,0,13));fence(root,(-16,0,3),(-16,0,13));fence(root,(23,0,7),(23,0,13))
    for xx,zz in [(-9.5,-6.8),(19.3,-6.8),(19.3,6.8)]:
        pipe(root,'Security camera bracket',[(xx,3,zz),(xx,3,zz-.5)],.03,'M_DarkMetal')
        item('Security camera',root,(xx,2.95,zz-.56),(.16,.15,.31),'M_Paper',rot=(22,0,0))
    root.script('EnvironmentAudio',f'  clip: {ref("Assets/_DesertShift/Audio/WashHum.wav",8300000,3)}\n  volume: 0.16\n  spatial: 1\n  range: 29\n')
    drip=Node('Dripping tap ambience',root,(3,1,0));drip.script('EnvironmentAudio',f'  clip: {ref("Assets/_DesertShift/Audio/Drips.wav",8300000,3)}\n  volume: 0.25\n  spatial: 1\n  range: 13\n')
    save_prefab(root,'Environment','PF_SunsetSplash_CarWash');save_prefab(od,'Interactables','PF_OfficeDoor');save_prefab(vend,'Props','PF_CoolCanyonMachine');save_prefab(dumpster,'Props','PF_Dumpster')
    return root

def fence(parent,a,b):
    a=np.array(a,dtype=float);b=np.array(b,dtype=float);delta=b-a;length=np.linalg.norm(delta);d=delta/length
    n=Node('Chain link fence',parent)
    count=int(length/2.6)
    for t in np.linspace(0,1,count+1):
        p=a+delta*t;item('Fence post',n,p+[0,1.05,0],(.07,2.1,.07),'M_Metal','Cylinder',coll=True)
    pipe(n,'Top rail',[a+[0,1.94,0],b+[0,1.94,0]],.025,'M_Metal')
    # One combined mesh, hundreds of diamonds, no alpha sorting.
    wire=Mesh()
    for direction in [-1,1]:
      for offset in np.arange(-2,length+2,.22):
        t0=max(0,(-offset)/direction) if direction>0 else max(0,offset-length)
        pts=[]
        for h in np.linspace(.13,1.88,17):
            along=offset+direction*h
            if 0<=along<=length:pts.append(a+d*along+np.array([0,h,0]))
        if len(pts)>1:wire.merge(tube(pts,.005,4))
    global seq;seq+=1;mn=f'FenceMesh_{seq}';save_mesh(mn,wire,'Environment/CarWash');Node('Diamond mesh',n).render(mn,'M_Metal',0)
    center=(a+b)/2+np.array([0,1,0]);ang=-math.degrees(math.atan2(delta[2],delta[0]))
    Node('Fence collision',n,center,(0,ang,0)).boxcollider((length,2,.06))
    n.script('DistanceDetail','  farCullHeight: 0.012\n')

def make_landscape(env):
    terrain=Node('Terrain_600m',env)
    for ix in range(6):
      for iz in range(6):
        name=f'DesertTile_{ix}_{iz}';save_mesh(name,terrain_tile(-300+ix*100,-300+iz*100),'Environment/Desert')
        surface(Node(name,terrain).render(name,'M_DesertGround').meshcollider(name),0)
    backdrop=Node('Distant ground apron',env)
    for ix in range(6):
      for iz in range(6):
        x0=-900+ix*300;z0=-900+iz*300
        if ix in [2,3] and iz in [2,3]:continue
        name=f'OuterGround_{ix}_{iz}';save_mesh(name,terrain_tile(x0,z0,300,20),'Environment/Desert')
        surface(Node(name,backdrop).render(name,'M_DesertGround').meshcollider(name),0)
    far=Node('DistantMountains',env)
    # Layered mesa silhouettes with eroded buttresses, following a distant semicircle.
    for i in range(19):
        angle=math.tau*i/19;r=RNG.uniform(410,590);x=math.cos(angle)*r;z=math.sin(angle)*r
        width=RNG.uniform(60,130);h=RNG.uniform(25,68)
        shape=Mesh();segs=28;rings=10
        for j in range(rings):
          yy=(j/(rings-1))*h
          for k in range(segs+1):
            a=k*math.tau/segs;radius=width*(.70-.29*(j/(rings-1))+.07*math.sin(a*6+i)+.035*math.sin(a*13+j*1.3))
            shape.v.append([math.cos(a)*radius,yy+2*math.sin(a*5+i),math.sin(a)*radius*.65]);shape.n.append([math.cos(a),.25,math.sin(a)]);shape.uv.append([k/segs,j/rings])
        for j in range(rings-1):
          for k in range(segs):
            q=j*(segs+1)+k;shape.t.extend([q,q+segs+1,q+1,q+1,q+segs+1,q+segs+2])
        # Top rock cap.
        ci=len(shape.v);shape.v.append([0,h-1,0]);shape.n.append([0,1,0]);shape.uv.append([.5,.5])
        for k in range(segs):shape.t.extend([ci,(rings-1)*(segs+1)+k+1,(rings-1)*(segs+1)+k])
        name=f'Mesa_{i:02d}';save_mesh(name,shape,'Environment/Desert')
        Node(name,far,(x,-4,z),(0,RNG.uniform(0,360),0)).render(name,'M_RockLight' if i%3==0 else 'M_Rock')
        for j in range(3):item('Eroded mesa foot',far,(x+RNG.uniform(-60,60),h*.16,z+RNG.uniform(-30,30)),(width*.8,h*.7,width*.5),'M_RockDark' if j==0 else 'M_RockLight',f'Rock_{j}')
    desert=Node('Desert rocks and scrub',env)
    # Small foliage is batched by material in 50m cells; substantial rocks keep simple collision.
    chunks={}
    for i in range(1850):
        x=RNG.uniform(-295,295);z=RNG.uniform(-295,295)
        if abs(z-float(road_z(x)))<9:continue
        if (x+77)**2+(z+18)**2<180 or (58<x<122 and -54<z<12):continue
        y=float(terrain_height(x,z));cell=(int((x+300)//50),int((z+300)//50))
        typ=RNG.random()
        if typ<.14:
            sz=RNG.uniform(.6,2.5);n=item('Weathered boulder',desert,(x,y+sz*.17,z),(sz,sz*.7,sz*.85),'M_RockLight',f'Rock_{RNG.randrange(7)}',(RNG.uniform(-15,15),RNG.uniform(0,360),0),coll=True)
            n.script('DistanceDetail','  farCullHeight: 0.016\n');continue
        name=f'Sage_{RNG.randrange(4)}' if typ<.58 else f'Grass_{RNG.randrange(3)}' if typ<.89 else 'Yucca'
        mat='M_Sage' if name.startswith('Sage') else 'M_Grass' if name.startswith('Grass') else 'M_Yucca'
        m=chunks.setdefault((cell,mat),Mesh());size=RNG.uniform(.55,1.7);m.merge(MESHES[name][1],(x,y,z),(size,size,size),(0,RNG.uniform(0,360),0))
    for ((cx,cz),mat),mesh in chunks.items():
        name=f'Scrub_{cx}_{cz}_{mat[2:]}';save_mesh(name,mesh,'Environment/Desert/Clusters')
        n=Node(name,desert).render(name,mat,0);n.script('DistanceDetail','  farCullHeight: 0.04\n')
    # Strong hero rocks and plants around the opening vista.
    for x,z,s in [(-90,12,5),(-103,25,7),(-52,-7,3.5),(-48,8,6),(-103,-31,3),(-89,41,8)]:
        item('Hero sandstone',desert,(x,float(terrain_height(x,z))+s*.2,z),(s,s*.65,s*.72),'M_RockLight',f'Rock_{int(s)%7}',(0,s*30,0),coll=True)
    road=Node('Connecting desert road',env)
    for x0 in range(-310,310,10):
        x=x0+5;z=float(road_z(x));slope=(float(road_z(x+.1))-float(road_z(x-.1)))/.2;angle=-math.degrees(math.atan(slope))
        surface(item('Asphalt ribbon',road,(x,.027,z),(10.04,.07,7.1),'M_Asphalt',rot=(0,angle,0),coll=True),5)
        for side in [-1,1]:
            item('Gravel shoulder',road,(x,.005,z+side*4.08),(10.04,.05,1.25),'M_Sand',rot=(0,angle,0))
            item('Edge stripe',road,(x,.073,z+side*3.04),(10.04,.012,.095),'M_WhitePaint',rot=(0,angle,0))
        for side in [-1,1]:item('Centre yellow',road,(x,.074,z+side*.105),(3.8,.012,.06),'M_YellowPaint',rot=(0,angle,0))
    # Wash driveway connects forecourt to the main road over the terrain.
    for zi in range(-52,-33,4):
        surface(item('Car wash access',road,(89,.07,zi),(11,.12,4.08),'M_Asphalt',coll=True),5)
    # Camp dirt access track follows the prepainted ground trail; subtle tire impressions.
    for zi in range(-59,-12,2):
        xx=-77+5*math.sin((zi+60)*.045);yy=float(terrain_height(xx,zi))+.028
        for sx in [-.8,.8]:item('Tire track',road,(xx+sx,yy,zi),(.12,.009,1.52),'M_DirtStain',rot=(0,-6,0))
    poles=Node('Utility poles and cables',road);positions=[]
    for i,x in enumerate(range(-280,300,42)):
        z=float(road_z(x))+9.7;y=float(terrain_height(x,z));positions.append(np.array([x,y+8,z]))
        n=Node('Power pole',poles,(x,y,z))
        item('Timber pole',n,(0,4.2,0),(.23,8.4,.23),'M_Wood','Cylinder',coll=True)
        item('Crossarm',n,(0,7.9,0),(.14,.16,2.4),'M_Wood')
        for zz in [-1,0,1]:item('Insulator',n,(0,8.10,zz),(.13,.22,.13),'M_Paper','Cylinder')
    for a,b in zip(positions,positions[1:]):
        for zz in [-1,0,1]:pipe(poles,'Sagging power cable',[a*(1-t)+b*t+np.array([0,-math.sin(t*math.pi)*1.45,zz]) for t in np.linspace(0,1,15)],.016,'M_DarkMetal')
    for x in [2,16,30,44,58]:
        z=float(road_z(x))-5.25;y=float(terrain_height(x,z))
        item('Guardrail post',road,(x,y+.55,z),(.13,1.1,.16),'M_Metal',coll=True)
    pipe(road,'Guardrail',[(x,.87,float(road_z(x))-5.25) for x in np.linspace(-3,63,24)],.105,'M_Metal')
    rs=Node('Car wash advance sign',road,(38,0,float(road_z(38))+8));item('Sign pole',rs,(0,1.5,0),(.075,3,.075),'M_Metal',coll=True);sign(rs,'ROAD_SIGN',(0,2.55,0),(2.8,1.4),180)
    # Damaged fence and isolated field observations lend story without exposition.
    for i in range(7):
        xx=-107+i*2.8;zz=-.7;yy=float(terrain_height(xx,zz));p=Node('Old fence section',desert,(xx,yy,zz),(0,0,8 if i==4 else 0))
        item('Old timber post',p,(0,.65,0),(.10,1.3,.10),'M_Wood',coll=True)
        if i!=3:
            for h in [.43,.97]:item('Fence rail',p,(1.35,h,0),(2.7,.075,.05),'M_Wood',rot=(0,0,-15 if i==4 else 0))
    for i in range(10):
        x=-62+i*.23;z=-21+i*.55;y=float(terrain_height(x,z))+.034
        item('Faded footprint',desert,(x+(-.14 if i%2 else .14),y,z),(.09,.004,.24),'M_DirtStain','Sphere',rot=(0,18,0))
    # Natural outer rock ridge, no invisible perimeter wall.
    for i in range(42):
        a=math.tau*i/42;xx=math.cos(a)*309;zz=math.sin(a)*309
        item('Boundary escarpment',desert,(xx,float(terrain_height(xx,zz))+3,zz),(RNG.uniform(16,27),RNG.uniform(10,20),RNG.uniform(13,22)),'M_Rock',f'Rock_{i%7}',(0,i*27,0),coll=True)
    return terrain,road
