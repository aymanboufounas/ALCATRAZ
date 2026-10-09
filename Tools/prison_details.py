"""Original prison furniture, world surface textures and precise card artwork."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import gaussian_filter
from geometry import *
from unity_writer import *
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def make_materials(texture):
 rng=np.random.default_rng(228);h=1024;n=rng.normal(0,1,(h,h));fine=gaussian_filter(n,.5);coarse=gaussian_filter(n,12);coarse/=max(coarse.std(),.01)
 value=np.clip(185+fine*4+coarse*2.8,150,215)
 concrete=texture('ConcreteFine',np.stack([value*.98,value*.98,value*.95],axis=-1))
 gy,gx=np.gradient(gaussian_filter(n,.8));normal=texture('ConcreteFine_Normal',np.stack([128-gx*4,128-gy*4,np.full_like(gx,254)],axis=-1),True)
 material('M_Concrete',[.8,.79,.75,1],.9,texture=concrete,normal=normal,tiling=3)
 material('M_Floor',[.63,.67,.65,1],.67,texture=concrete,normal=normal,tiling=17)
 # Seamless aggregate. Fine cracks and restrained expansion joints, no large cloudy patches.
 yard=np.stack([value*.82,value*.82,value*.78],axis=-1)
 for v in [0,256,512,768]:yard[max(0,v-2):v+2,:,:]*=.90;yard[:,max(0,v-2):v+2,:]*=.90
 yt=texture('YardPavers',yard);material('M_Yard',[.79,.78,.74,1],.87,texture=yt,normal=normal,tiling=16)
 material('M_WallPaint',[.38,.47,.42,1],.84,texture=concrete,tiling=2)
 material('M_Plaster',[.89,.87,.80,1],.91,texture=concrete,tiling=2)
 material('M_Trim',[.22,.29,.27,1],.48,.3)
 material('M_Grass',[.25,.31,.20,1],.99)
 material('M_Felt',[.065,.24,.17,1],.97)
 material('M_WindowGlow',[.63,.77,.85,1],.2,emission=[.35,.45,.5,1])
 material('M_RV_Rubber',[.048,.053,.055,1],.88)
 material('M_EyeWhite',[.81,.80,.71,1],.28)
 material('M_Iris',[.20,.24,.21,1],.2)
 material('M_Pupil',[.018,.02,.021,1],.25)
 material('M_EyeSocket',[.26,.20,.16,1],.91)
 material('M_SkinCrease',[.35,.23,.16,1],.88)
 material('M_Lips',[.47,.28,.23,1],.85)
 material('M_MouthLine',[.20,.12,.10,1],.93)
 material('M_Hair',[.050,.039,.031,1],.83)
 material('M_GreyHair',[.28,.28,.27,1],.92)
 material('M_Stubble',[.25,.22,.18,1],.91)
 material('M_Nails',[.56,.45,.38,1],.68)
 yy,xx=np.mgrid[:h,:h];weave=((xx%8<2)*.7+(yy%8<2)*.5)
 cloth=np.clip(208+n*1.8+weave*5,180,235);ct=texture('PrisonClothWeave',np.stack([cloth,cloth,cloth],-1))
 for name,color in {'PrisonBlue':[.23,.34,.40,1],'PrisonGrey':[.48,.47,.43,1],'PrisonBurgundy':[.33,.18,.16,1],'PrisonSand':[.65,.53,.36,1],'PrisonCream':[.72,.70,.62,1],'GuardUniform':[.15,.22,.28,1],'RivalUniform':[.33,.28,.24,1],'BrotherClothes':[.28,.42,.47,1],'Trousers':[.28,.32,.33,1]}.items():
  material('M_'+name,color,.94,texture=ct,tiling=3)
 for name,color in [('PrisonOrange',[.97,.46,.09,1]),('PrisonOrangeTrousers',[.88,.38,.07,1])]:material('M_'+name,color,.94,texture=ct,tiling=3)
 for name,lines in [('EliasFrontID',['VALE','B-04']),('EliasBackID',['INMATE','ELIAS VALE / B-04'])]:
  im=Image.new('RGB',(1024,512),(217,120,33));d=ImageDraw.Draw(im)
  for i,text in enumerate(lines):
   font=ImageFont.truetype(FONT,148 if i==0 else 65);bounds=d.textbbox((0,0),text,font=font);width=bounds[2]-bounds[0]
   d.text(((1024-width)/2,40 if i==0 else 310),text,font=font,fill=(25,29,27))
  material('M_'+name,[1,1,1,1],.94,texture=texture(name,np.array(im)))
 for name,color in {'Olive':[.61,.44,.31,1],'Tan':[.65,.43,.28,1],'Deep':[.25,.15,.10,1],'Light':[.78,.60,.46,1],'Brown':[.44,.27,.17,1]}.items():
  st=np.clip(237+n*1.3,225,246);path=texture('SkinPores_'+name,np.stack([st,st,st],-1));material('M_Skin'+name,color,.76,texture=path)
  material('M_Stubble'+name,[color[0]*.79,color[1]*.79,color[2]*.79,1],.91,texture=path)
  material('M_Beard'+name,[color[0]*.27,color[1]*.27,color[2]*.27,1],.93,texture=path)
 for name,color in {'Undershirt':[.76,.74,.66,1],'Seam':[.34,.39,.40,1],'PrisonPatch':[.82,.79,.67,1],'Belt':[.13,.16,.16,1],'Shoe':[.09,.10,.11,1],'Sole':[.29,.29,.27,1],'Laces':[.50,.49,.44,1]}.items():material('M_'+name,color,.86)
 material('M_ChipRed',[.61,.17,.13,1],.54);material('M_ChipBlue',[.15,.31,.43,1],.54);material('M_ChipCream',[.77,.73,.57,1],.54)
 # Exact standard 52-card designs, shared by world props and the playable UI.
 font=ImageFont.truetype(FONT,43);small=ImageFont.truetype(FONT,31);big=ImageFont.truetype(FONT,81)
 for c in range(52):
  rank=c%13+2;label={11:'J',12:'Q',13:'K',14:'A'}.get(rank,str(rank));suit=['♣','♦','♥','♠'][c//13];red=c//13 in [1,2]
  im=Image.new('RGB',(256,356),(231,229,215));d=ImageDraw.Draw(im);d.rounded_rectangle((4,4,251,351),radius=13,outline=(125,121,108),width=3);color=(150,31,28) if red else (28,38,41)
  d.text((20,9),label,font=font,fill=color);d.text((22,55),suit,font=small,fill=color);d.text((128,175),suit,font=big,fill=color,anchor='mm')
  corner=im.crop((12,7,78,103)).rotate(180);im.paste(corner,(178,253))
  path='Assets/Game/Resources/Blackstone/Cards/card_'+str(c).zfill(2)+'.png';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
  meta(path,'TextureImporter','  serializedVersion: 13\n  isReadable: 0\n  textureType: 0\n  mipmaps:\n    enableMipMap: 1\n  maxTextureSize: 512\n  textureSettings:\n    filterMode: 1\n    aniso: 4\n    wrapU: 1\n    wrapV: 1\n')
  material('M_Card_'+str(c).zfill(2),[1,1,1,1],.83,texture=path)
 im=Image.new('RGB',(256,356),(40,66,73));d=ImageDraw.Draw(im);d.rounded_rectangle((7,7,248,348),radius=10,outline=(181,163,106),width=5)
 for x in range(22,240,16):
  for y in range(24,340,16):d.line([(x-5,y),(x,y-6),(x+5,y),(x,y+6),(x-5,y)],fill=(78,111,117),width=1)
 path='Assets/Game/Resources/Blackstone/Cards/back.png';im.save(ROOT/path);meta(path,'TextureImporter','  serializedVersion: 13\n  isReadable: 0\n  maxTextureSize: 512\n')
 material('M_CardBack',[1,1,1,1],.83,texture=path)

def decorate(env,lights,box_node,mesh_node,sign,light):
 # Cream and sage walls, reinforcing frames, small pipework and readable landmarks.
 for z in [-27,-23,-19,-15,-11,-7,-3]:
  box_node('Cell wall lower paint',env,(-10.01,.7,z),(.035,1.4,3.82),'M_WallPaint',False)
  box_node('Cell wall upper plaster',env,(-10.00,2.3,z),(.034,1.7,3.82),'M_Plaster',False)
  for x in [-3.4,3.4]:box_node('Corridor beam',env,(x,3.15,z),(.17,.25,.23),'M_Trim',False)
  light(lights,'Cell soft fill',(-7.4,2.65,z),2.1,5,(1,.91,.77),2)
 box_node('East wall lower paint',env,(11.27,.75,-13),(.04,1.5,33.4),'M_WallPaint',False)
 box_node('East wall plaster',env,(11.25,2.4,-13),(.04,1.6,33.4),'M_Plaster',False)
 for z in [-24,-16,-8,0]:
  box_node('High frosted window',env,(11.20,2.65,z),(.03,.8,1.8),'M_WindowGlow',False)
  for dz in [-.84,-.4,0,.4,.84]:box_node('Window security rail',env,(11.15,2.65,z+dz),(.06,.84,.03),'M_Metal',False)
  light(lights,'Window daylight bounce',(8.9,2.3,z),4.2,10,(.87,.94,1),2)
 for z in [9,17,25,33]:
  box_node('West yard wall lower paint',env,(-17.93,1.0,z),(.04,1.95,7.7),'M_WallPaint',False)
  box_node('East yard wall lower paint',env,(17.92,1.0,z),(.04,1.95,7.7),'M_WallPaint',False)
 for x in [-15,-9,-3,3,9,15]:
  box_node('Yard wall coping',env,(x,4.6,40.27),(5.94,.13,.66),'M_Trim',False)
  for dz in [-.1,.12]:mesh_node('Perimeter wire',env,(x,4.90,40.26+dz),(5.97,.032,.032),'M_DarkMetal',collision=False)
 for z in [8.5,38.3]:
  box_node('Painted yard line',env,(0,.04,z),(30,.008,.06),'M_PrisonPatch',False)
 for x in [-15.2,15.2]:box_node('Painted yard sideline',env,(x,.04,23.4),(.06,.008,30),'M_PrisonPatch',False)
 # A basketball half court, preserving the mission-fight area at (6,21).
 box_node('Basketball post',env,(10,2.4,36),(.17,4.8,.17),'M_Trim')
 box_node('Basketball backboard',env,(10,4.65,35.6),(1.8,.95,.09),'M_Ceramic',False)
 box_node('Backboard target top',env,(10,4.65,35.54),(.66,.04,.008),'M_Trim',False)
 for x in [9.68,10.32]:box_node('Backboard target side',env,(x,4.45,35.54),(.04,.43,.008),'M_Trim',False)
 save_mesh('BasketballRim',torus(.225,.016,32,8),'Props');mesh_node('Basketball rim',env,(10,4.28,35.24),(1,1,1),'M_Rust','BasketballRim',collision=False)
 for i in range(14):
  a=i*math.tau/14
  mesh_node('Hoop net string',env,(10+math.cos(a)*.16,4.02,35.24+math.sin(a)*.16),(.008,.45,.008),'M_PrisonPatch',collision=False)
 # Weight rack and movable-looking dumbbells.
 box_node('Weight rack shelf',env,(-13,1.00,34),(2,.09,.65),'M_Metal')
 for x in [-13.8,-12.2]:box_node('Rack leg',env,(x,.48,34),(.09,.96,.12),'M_Trim')
 for x in [-13.55,-13,-12.45]:
  mesh_node('Dumbbell handle',env,(x,1.11,34),(.20,.035,.035),'M_Chrome',collision=False)
  for dx in [-.14,.14]:mesh_node('Dumbbell weight',env,(x+dx,1.11,34),(.095,.15,.15),'M_DarkMetal','PrisonCylinder',rot=(0,0,90),collision=False)
 for z in [14,29]:
  mesh_node('Yard litter bin',env,(-17.2,.46,z),(.51,.9,.51),'M_WallPaint','PrisonCylinder',collision=False)
 sign(env,'RecHours',(1,2.45,4.13),'RECREATION YARD\nCOUNT AT NEXT WHISTLE',(3.4,.7))
 sign(env,'CardArea',(-8,2.1,16),'YARD TABLES',(1.7,.35),(0,180,0))

def chair(parent,pos,yaw,box_node):
 root=Node('Welded steel chair',parent,pos,(0,yaw,0))
 box_node('Chair seat',root,(0,.46,0),(.50,.065,.48),'M_Wood',False)
 box_node('Chair back',root,(0,.77,-.23),(.49,.26,.055),'M_Wood',False)
 for x in [-.20,.20]:
  for z in [-.19,.19]:box_node('Chair leg',root,(x,.23,z),(.034,.46,.034),'M_Metal',False)
 root.boxcollider((.47,.52,.46),(0,.25,0))
 return root

def tables(env,box_node,mesh_node,sign):
 poker=Node('Five-card draw table',env,(-6,.0,20),static=False)
 box_node('Poker top',poker,(0,.78,0),(2.55,.12,1.35),'M_Wood')
 box_node('Green felt',poker,(0,.847,0),(2.38,.013,1.20),'M_Felt',False)
 for x in [-.97,.97]:
  for z in [-.48,.48]:box_node('Table welded leg',poker,(x,.37,z),(.055,.75,.055),'M_Metal',False)
 for x in [-.59,.59]:
  for z,yaw in [(-1.07,0),(1.07,180)]:chair(poker,(x,0,z),yaw,box_node)
 for i,c in enumerate([12,25,35,42,1]):mesh_node('Face-up playing card',poker,(-.25+i*.12,.863,0),(.095,1,.136),'M_Card_'+str(c).zfill(2),'PrisonPlane',rot=(0,i*4-8,0),collision=False)
 for x,z in [(-.60,-.43),(.58,-.43),(-.60,.43),(.58,.43)]:
  for i in range(3):mesh_node('Covered hand',poker,(x+i*.037,.864+i*.001,z),(.095,1,.136),'M_CardBack','PrisonPlane',rot=(0,i*12-12,0),collision=False)
 for x,z,mat in [(-.72,-.2,'M_ChipRed'),(.84,.2,'M_ChipBlue'),(-.95,.2,'M_ChipCream')]:
  for i in range(5):mesh_node('Friendly-game counter',poker,(x,.87+i*.007,z),(.041,.006,.041),mat,'PrisonCylinder',collision=False)
 poker.boxcollider((2.7,.55,1.45),(0,.67,0))
 talk=Node('Conversation table',env,(-7,.0,14.5),static=False)
 box_node('Conversation table top',talk,(0,.75,0),(2.25,.12,1.1),'M_Wood')
 for x in [-.86,.86]:box_node('Conversation table support',talk,(x,.36,0),(.075,.72,.70),'M_Metal',False)
 for x in [-.52,.52]:
  for z,yaw in [(-.91,0),(.91,180)]:chair(talk,(x,0,z),yaw,box_node)
 for x in [-.53,.51]:
  mesh_node('Steel coffee cup',talk,(x,.862,.1),(.10,.13,.10),'M_Ceramic','PrisonCylinder',collision=False)
 box_node('Folded newspaper',talk,(0,.821,.07),(.43,.012,.30),'M_Paper',False)
 talk.boxcollider((2.5,.6,1.25),(0,.61,0))
 return poker,talk
