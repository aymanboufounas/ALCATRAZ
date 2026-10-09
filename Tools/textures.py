from PIL import Image,ImageDraw,ImageFont,ImageFilter
from scipy.ndimage import gaussian_filter
import numpy as np
from unity_writer import *

def texmeta(path,normal=False):
    meta(path,'TextureImporter',f'''  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 1
    sRGBTexture: {0 if normal else 1}
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
  isReadable: 0
  streamingMipmaps: 1
  textureType: {1 if normal else 0}
  textureShape: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 4
    mipBias: 0
    wrapU: 0
    wrapV: 0
    wrapW: 0
  nPOTScale: 0
  alphaSource: 1
  alphaIsTransparency: 0
  textureCompression: 1
''')

def save_image(name,im,normal=False):
    import io,os
    path=f'{ART}/Textures/{name}.png';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    data=io.BytesIO();im.save(data,format='PNG');temp=p.with_suffix('.tmp');temp.write_bytes(data.getvalue());os.replace(temp,p)
    texmeta(path,normal);return path

def noise_texture(name,kind,size=512):
    rng=np.random.default_rng(sum(map(ord,name)));r=rng.random((size,size))
    noise=.45+gaussian_filter(r,3)*.7+(r-.5)*.15
    y,x=np.indices((size,size))
    if kind=='metal':noise+=.025*np.sin(y*1.8);noise-=.06*np.maximum(0,np.sin(x*.04+y*.008))**14
    if kind=='wood':noise+=.055*np.sin(x*.35+3*np.sin(y*.018))+ .025*np.sin(x*.85+y*.005)
    if kind=='cloth':noise+=.045*(np.sin(x*np.pi/2)+np.sin(y*np.pi/2))
    if kind=='stucco':noise+=(r-.5)*.12
    if kind=='rubber':noise+=.06*np.sin(x*.12)*np.sin(y*.6)
    if kind=='concrete':noise+=.16*(gaussian_filter(r,20)-.5)
    if kind=='asphalt':noise=.68+(r-.5)*.3
    noise=np.clip(noise,0,1);rgb=np.repeat((noise*255).astype('uint8')[:,:,None],3,axis=2)
    base=save_image(name+'_Base',Image.fromarray(rgb))
    dx,dy=np.gradient(gaussian_filter(noise, .6));normal=np.stack([-dy*2,-dx*2,np.ones_like(dx)],2);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
    nm=save_image(name+'_Normal',Image.fromarray(((normal*.5+.5)*255).astype('uint8')),True)
    return base,nm

def label(name,lines,bg='#203d41',fg='#f4db9e',size=(1024,512)):
    im=Image.new('RGB',size,bg);d=ImageDraw.Draw(im)
    d.rounded_rectangle((15,15,size[0]-16,size[1]-16),radius=22,outline=fg,width=5)
    candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf']
    fontpath=next((p for p in candidates if Path(p).exists()),'DejaVuSans-Bold.ttf')
    for text,y,fs in lines:
        f=ImageFont.truetype(fontpath,fs);box_=d.textbbox((0,0),text,font=f);tw=box_[2]-box_[0]
        d.text(((size[0]-tw)/2,y),text,font=f,fill=fg)
    rng=np.random.default_rng(76)
    for i in range(90):
        x=int(rng.uniform(0,size[0]));y=int(rng.uniform(0,size[1]));d.line([(x,y),(x+int(rng.uniform(4,25)),y-2)],fill=bg,width=1)
    return save_image(name,im)

def build_materials():
    maps={k:noise_texture(k.title(),k) for k in ['metal','wood','cloth','stucco','rubber','concrete','asphalt']}
    def m(name,c,k='stucco',rough=.8,metal=0,alpha=1,em=None):
        material(name,[*c,alpha],rough,metal,*maps[k],emission=em,transparent=alpha<1)
    m('M_Sand',(.70,.59,.43));m('M_Rock',(.53,.31,.17));m('M_RockLight',(.68,.45,.27))
    m('M_RockDark',(.34,.24,.19));m('M_Asphalt',(.12,.14,.15),'asphalt',.95)
    m('M_Concrete',(.52,.50,.43),'concrete');m('M_WetConcrete',(.20,.28,.28),'concrete',.22)
    m('M_RV_Body',(.93,.79,.51),'metal',.53);m('M_RV_Upper',(.98,.91,.7),'metal',.5)
    m('M_RV_Stripe',(.68,.26,.10),'metal',.58);m('M_RV_StripeDark',(.36,.18,.10),'metal')
    m('M_RV_Rubber',(.045,.045,.039),'rubber',.92);m('M_RV_Glass',(.20,.35,.36),'metal',.09,.25,.26)
    m('M_CarWashStucco',(.83,.72,.52),'stucco');m('M_Turquoise',(.13,.46,.43),'metal',.47)
    m('M_FadedRed',(.58,.19,.12),'metal');m('M_Metal',(.38,.41,.39),'metal',.38,.78)
    m('M_Chrome',(.70,.74,.72),'metal',.22,.88);m('M_DarkMetal',(.1,.13,.13),'metal',.54,.65)
    m('M_Plastic',(.18,.30,.31),'rubber',.62);m('M_PlasticOrange',(.78,.30,.1),'rubber',.68)
    m('M_Wood',(.43,.27,.14),'wood');m('M_InteriorWood',(.65,.43,.22),'wood',.65)
    m('M_Paper',(.85,.81,.62),'cloth');m('M_ChairFabric',(.48,.44,.24),'cloth')
    m('M_Grass',(.56,.48,.27),'cloth');m('M_Sage',(.32,.39,.26),'cloth');m('M_Yucca',(.22,.31,.20),'cloth')
    m('M_WhitePaint',(.89,.84,.61),'metal');m('M_YellowPaint',(.90,.61,.12),'metal')
    m('M_CharacterSkin',(.70,.44,.29),'cloth',.87)
    m('M_CharacterClothes',(.76,.67,.48),'cloth',.91);m('M_Shirt',(.26,.35,.21),'cloth')
    m('M_Trousers',(.37,.29,.19),'cloth');m('M_Hair',(.19,.15,.11),'cloth')
    m('M_EyeWhite',(.82,.78,.65),'metal',.45);m('M_Iris',(.16,.19,.12),'metal',.35)
    m('M_Light',(.92,.86,.65),'metal',.3,em=[1.4,1.2,.8,1]);m('M_RedLight',(.6,.12,.06),'metal',.32,em=[.7,.1,.02,1])
    m('M_Puddle',(.23,.34,.34),'concrete',.10,.20,.58);m('M_Foam',(.86,.89,.80),'concrete',.68,.0,.7)
    m('M_DirtStain',(.27,.19,.11),'concrete',.9,.0,.42)
    m('M_BlueGlass',(.08,.43,.52),'metal',.16,.15,.6)
    specs=[('SUNSET_SPLASH',[('SUNSET',80,142),('SPLASH',215,142),('CAR WASH  /  EST. 1984',410,37)],'#17484b','#f4d39b'),
           ('ROAD_SIGN',[('SUNSET SPLASH',90,88),('SELF SERVICE',230,74),('TURN RIGHT  >',360,57)],'#254a4b','#e2dbbc'),
           ('RV_BADGE',[('SUNDOWNER',100,103),('M O T O R  C O A C H',295,40)],'#392a1c','#e9d39e'),
           ('LICENSE',[('NEW SUNDUST',52,62),('DS - 0842',163,125),('LAND OF QUIET ROADS',373,42)],'#e5c37e','#403a30'),
           ('BAY_RULES',[('RINSE / FOAM / SHINE',95,61),('KEEP THE BAY CLEAR',240,54),('SUNSET SPLASH',385,36)],'#e9d8ad','#244545'),
           ('OFFICE',[('OFFICE',95,142),('PLEASE RING ONCE',328,52)],'#23464a','#f3d5a1'),
           ('STAFF',[('STAFF ROOM',165,103)],'#23464a','#f3d5a1'),
           ('STORAGE',[('STORAGE',165,120)],'#23464a','#f3d5a1'),
           ('UTILITY',[('UTILITY',95,142),('AUTHORIZED STAFF',330,50)],'#ad6536','#f3dfb7'),
           ('RESTROOM',[('RESTROOM',165,107)],'#23464a','#f3d5a1'),
           ('VENDING',[('COOL',80,157),('CANYON',245,107),('SODA  /  WATER',404,44)],'#b54f2a','#f4d99f'),
           ('NOTEBOOK',[('CALDER',77,104),('FIELD OBSERVATIONS',236,58),('DUST / WATER / LIGHT',375,40)],'#556142','#ead8b4'),
           ('MONITOR',[('SUNSET SPLASH',63,68),('CAM 01     CAM 02',198,55),('SIGNAL STABLE',337,46)],'#182c2c','#77a89b')]
    for name,lines,bg,fg in specs:
        texture=label(name,lines,bg,fg);material('M_Sign_'+name,[1,1,1,1],.72,texture=texture)
    # A unique world-space colour map prevents repeating terrain patches.
    s=2048;rng=np.random.default_rng(41);a=rng.random((s,s));n=gaussian_filter(a,35);n=(n-n.min())/(n.max()-n.min());fine=gaussian_filter(a,1)
    xx,zz=np.meshgrid(np.linspace(-300,300,s),np.linspace(300,-300,s))
    blend=np.clip(.2+.5*n+.3*np.sin(xx*.03+zz*.024)**2,0,1)
    sand=np.array([181,150,107]);rock=np.array([148,120,88]);rgb=sand[None,None,:]*(1-blend[:,:,None])+rock[None,None,:]*blend[:,:,None]
    from geometry import road_z
    dist=np.abs(zz-road_z(xx));rgb-=np.exp(-(dist/8)**2)[:,:,None]*9
    # Worn, winding camp trail with twin wheel paths.
    trailx=-77+5*np.sin((zz+60)*.045);td=np.abs(xx-trailx)
    trail=np.exp(-(td/3.7)**6)*(zz>-60)*(zz<-7)
    rgb+=trail[:,:,None]*11
    rgb-=((np.exp(-((td-.8)/.16)**2))*trail)[:,:,None]*13
    rgb+=(fine-.5)[:,:,None]*22
    base=save_image('DesertGround_World_2K',Image.fromarray(np.uint8(np.clip(rgb,0,255))))
    material('M_DesertGround',[1,1,1,1],.98,texture=base,normal=maps['concrete'][1])
    return maps
