"""Offline native-geometry and menu-layout previews; not Unity screenshots."""
import json,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import render_supplied_previews as r
from render_current_previews import cube,placed
OUT=r.ROOT/'Documentation/Revision12Previews';OUT.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BASE=r.ROOT/'Assets/Game/Supplied/Resources/AlcatrazExtras'
def native(name):
    root=BASE/name;materials={};textures={}
    for p in root.rglob('*.meta'):
        match=re.search(r'guid: (\w+)',p.read_text())
        if match:textures[match[1]]=Path(str(p)[:-5])
    for p in (root/'Materials').glob('*.mat'):
        source=p.read_text();name_mat=re.search(r'm_Name: (.*)',source)[1]
        tex=re.search(r'- _BaseMap:\s+m_Texture: \{fileID: \d+, guid: (\w+)',source)
        color=re.search(r'- _BaseColor: \{r: ([\d.e-]+), g: ([\d.e-]+), b: ([\d.e-]+), a: ([\d.e-]+)',source)
        materials[name_mat]=(textures.get(tex[1]) if tex else None,list(map(float,color.groups())) if color else [1,1,1,1])
    result=[]
    for p in (root/'Meshes').glob('*.asset'):
        source=p.read_text();raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',source)[1]);v=np.frombuffer(raw,'<f4').reshape(-1,12)
        indices=bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)',source)[1]);wide=int(re.search(r'm_IndexFormat: (\d+)',source)[1]);tri=np.frombuffer(indices,'<u4' if wide else '<u2').reshape(-1,3)
        key=p.stem.rsplit('_',1)[0];texture,color=materials[key];uv=v[:,10:12].copy();uv[:,1]=1-uv[:,1]
        result.append(r.mesh(v[:,:3],tri,uv=uv,normal=v[:,3:6],path=texture,color=color))
    return result

def mark(image,label):
    d=ImageDraw.Draw(image);d.rectangle((0,0,image.width,55),fill=(15,24,30));d.text((24,16),label+'  /  OFFLINE PREVIEW — NOT UNITY',font=ImageFont.truetype(FONT,17),fill=(224,214,185));return image

def menu():
    image=Image.new('RGB',(1920,1080),(15,21,28));d=ImageDraw.Draw(image)
    d.rectangle((0,0,620,1080),fill=(7,10,12));d.line((620,0,620,1080),fill=(97,82,52))
    gold=(212,173,99);paper=(237,232,217)
    def text(x,y,s,size=21,color=paper):d.multiline_text((x,y),s,font=ImageFont.truetype(FONT,size),fill=color,spacing=14)
    text(70,70,'THE SILENT BLUEPRINT',15,gold);text(64,140,'PAUSED',68);text(70,315,'SESSION PAUSED  /  CELLHOUSE',15,gold);d.line((70,357,540,357),fill=(125,102,58))
    for i,name in enumerate(['01   Resume game','02   Chapter 01','03   Island locations','04   Settings','05   Controls','06   Return to title']):
        y=410+i*76;d.rectangle((70,y,540,y+60),fill=(31,38,43));text(92,y+15,name,23)
    text(70,1002,'ELIAS VALE  ·  INMATE B-04',15,gold)
    text(700,197,'CHAPTER 01  /  THE PRISONER',15,gold);text(700,250,'A way out begins here.',46)
    text(700,370,'Discover the island, meet the inmates and learn the\nprison routine. Build alliances. Find your route to freedom.')
    d.line((700,600,1850,600),fill=(58,64,70));text(700,651,'AVAILABLE ON THE ISLAND',15,gold)
    text(700,710,'Cellhouse & galleries  ·  Coastal patrol boat\nHelicopter flight  ·  Boxing training  ·  Texas Hold’em')
    text(1500,1002,'ALCATRAZ  /  CHAPTER 01',15,gold)
    mark(image,'MENU LAYOUT FROM CODE').save(OUT/'Menu.png')

def main():
    menu()
    scene=placed(native('PokerTable'),1.2,(0,0,0))+placed(native('PokerProps'),.32,(0,.85,0))
    scene+= [cube('Floor',(0,-.15,0),(10,.3,10),(.43,.46,.45,1))]
    mark(r.render(scene,size=(1280,720),eye=(3.4,2.9,-4.2),center=(0,.7,0)), 'SUPPLIED POKER TABLE').save(OUT/'PokerTable.png')
    scene=placed(native('UtilityBuilding'),6,(0,0,0))+placed(native('BridgePack'),2.5,(8,0,2))
    scene+=[cube('Floor',(0,-.2,0),(35,.4,30),(.43,.46,.45,1))]
    mark(r.render(scene,size=(1280,720),eye=(21,14,-25),center=(3,2,0)),'SUPPLIED INDUSTRIAL BUILDING & BRIDGE').save(OUT/'Buildings.png')
if __name__=='__main__':main()
