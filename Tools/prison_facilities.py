"""Revision 04: connected cell galleries and usable inmate facilities.
The B-04 spawn, story roles, NPC routes and activity seats stay in place.
"""
import math
import numpy as np
from geometry import Mesh,tube
from unity_writer import Node,save_mesh

def expand(env,lights,box_node,mesh_node,sign,light,colliders):
    root=Node('_PrisonFacilities')
    def disable(name):
        for n in Node.all:
            if n.name==name:n.active=False
        colliders[:]=[c for c in colliders if c[0]!=name]
    def relocate(name,pos=None,size=None):
        for n in Node.all:
            if n.name!=name:continue
            old=np.array(n.pos)
            if pos is not None:n.pos=list(pos)
            if size is not None:n.scale=list(size)
            for i,(label,p,s) in enumerate(colliders):
                if label==name and np.allclose(p,old):
                    colliders[i]=(label,np.array(n.pos),np.array(n.scale));break
    def collision_slab(name,pos,size):
        n=box_node(name,root,pos,size,'M_DarkMetal')
        n.parts=[part for part in n.parts if part[0] not in [23,33]]
        return n
    def plaque(name,pos,text,size=(2.5,.7),rot=(0,180,0)):
        return sign(root,name,pos,text,size,rot)

    # Raise the roof and envelope to make a real two-storey cell block.
    relocate('Cell block roof',(0,7.27,-13),(23,.30,34))
    relocate('Cell block roof cap',(0,7.52,-13),(23.7,.22,34.5))
    relocate('Cell block east wall',(11.5,3.61,-13),(.42,7.22,34))
    relocate('Cell block south wall',(0,3.61,-30),(23,7.22,.42))
    for n in Node.all:
        if n.name=='Cell chimney':n.pos[1]=8.28
    box_node('Upper block north wall',root,(0,5.42,4),(23,3.62,.30),'M_Concrete')
    level=3.57
    for side in [-1,1]:
        x=-7.15 if side<0 else 7.75;width=6.3 if side<0 else 7.5
        box_node('Upper cell floor',root,(x,level+.02,-13),(width,.15,34),'M_Floor')
        box_node('Upper gallery deck',root,(side*3.08,level+.02,-13),(1.84,.15,34),'M_Floor')
        # Leave the bridge entrance open between z=.86 and z=3.1.
        for centre,length in [(-14.52,30.76),(3.475,.75)]:
            collision_slab('Upper gallery safety barrier',(side*2.16,level+.65,centre),(.10,1.1,length))
            for y in [level+.36,level+1.2]:
                box_node('Upper gallery handrail',root,(side*2.16,y,centre),(.065,.055,length),'M_Metal',False)
        for z in np.arange(-28.7,3.2,1.45):
            if .86<z<3.1:continue
            mesh_node('Upper gallery rail post',root,(side*2.16,level+.73,float(z)),(.06,1.1,.06),'M_Metal','PrisonCylinder',collision=False)
        for i in range(8):
            z=-27+i*4;number=('B' if side<0 else 'C')+'-'+str(i+9).zfill(2)
            cell=Node('Upper cell '+number,root)
            box_node('Upper cell partition',cell,(x,level+1.75,z-2),(width,3.5,.22),'M_Concrete')
            box_node('Upper cell back',cell,((-10.2 if side<0 else 11.3),level+1.75,z),(.24,3.5,4),'M_Concrete')
            mesh_node('Upper locked cell bars',cell,(side*4,level,z),(1,1,2.8),'M_Metal','FixedBars',collision=False)
            collision_slab('Upper locked cell collision',(side*4,level+1.3,z),(.11,2.6,4))
            box_node('Upper cell lintel',cell,(side*4,level+2.88,z),(.30,.45,4),'M_WallPaint')
            bedx=-8.6 if side<0 else 9
            box_node('Upper bed frame',cell,(bedx,level+.37,z),(1.2,.13,2.15),'M_Metal',False)
            box_node('Upper cell mattress',cell,(bedx,level+.52,z),(1.16,.20,2.07),'M_Cloth')
            box_node('Upper cell pillow',cell,(bedx,level+.67,z+.71),(.77,.13,.43),'M_Cloth',False)
            for dx in [-.46,.46]:
                for dz in [-.95,.95]:box_node('Upper bed leg',cell,(bedx+dx,level+.19,z+dz),(.055,.38,.055),'M_Metal',False)
            tx=-5.7 if side<0 else 5.7
            box_node('Upper cell table',cell,(tx,level+.74,z+1.3),(.92,.10,.6),'M_Metal')
            box_node('Upper cell stool',cell,(tx,level+.34,z+.6),(.38,.65,.38),'M_Wood')
            mesh_node('Upper cell toilet',cell,((-9.15 if side<0 else 10.3),level+.3,z-1.35),(.60,.4,.70),'M_Ceramic','PrisonSphere',collision=False)
            plaque('Cell plate '+number,(side*3.76,level+2.64,z),number,(.72,.25),(0,90 if side<0 else -90,0))
        for z in [-25,-17,-9,-1]:
            box_node('Gallery fluorescent housing',root,(side*3.08,6.83,z),(.3,.10,1.4),'M_DarkMetal',False)
            box_node('Gallery fluorescent diffuser',root,(side*3.08,6.77,z),(.22,.06,1.25),'M_Lamp',False)
            light(lights,'Gallery corridor lamp',(side*3.08,6.45,z),4.0,9,(.92,.95,1))

    # The new stairs leave both ground-level aisles clear.
    for i in range(21):
        height=(i+1)*.17
        box_node('Gallery stair '+str(i+1).zfill(2),root,(0,.095+height/2,-6.7+(i+.5)*.36),(1.9,height,.36),'M_Concrete')
    box_node('Upper gallery landing',root,(0,level+.02,1.98),(4.4,.15,2.24),'M_Floor')
    for side in [-1,1]:
        points=[(side*1.04,1.24,-6.52),(side*1.04,4.64,.68)]
        name='StairHandrail'+str(side);save_mesh(name,tube(points,.032,10),'Environment/PrisonFacilities')
        mesh_node('Stair handrail',root,(0,0,0),(1,1,1),'M_Metal',name,collision=False)
    plaque('Upper gallery directions',(0,6.4,3.80),'CELL BLOCK B / C\nUPPER GALLERY',(4.2,.72))
    plaque('Stair directions',(.99,1.55,-6.6),'UPPER\nGALLERY',(.6,.7),(0,-90,0))
    # Finish the former placeholder C-row cells on the ground floor.
    for i in range(8):
        z=-27+i*4
        plaque('Cell plate C-'+str(i+1).zfill(2),(3.76,2.6,z),'C-'+str(i+1).zfill(2),(.72,.25),(0,-90,0))
        box_node('C row bed frame',root,(9,.38,z),(1.22,.13,2.10),'M_Metal',False)
        box_node('C row pillow',root,(9,.70,z+.71),(.72,.13,.42),'M_Cloth',False)
        box_node('C row writing shelf',root,(5.75,.75,z+1.3),(1.12,.10,.65),'M_Metal')
        mesh_node('C row toilet',root,(10.35,.29,z-1.25),(.6,.4,.70),'M_Ceramic','PrisonSphere',collision=False)
    for z in [-26,-18,-10,-2]:
        for x in [-.65,.65]:box_node('Suspended lamp cable',root,(x,5.15,z),(.017,3.85,.017),'M_DarkMetal',False)

    # Replace two solid scenery blocks with rooms the inmate can walk into.
    def room(old,label,cx,cz,width,depth):
        for suffix in [' walls',' stone foundation',' door',' sign']:disable(old+suffix)
        relocate(old+' roof',(cx,3.73,cz),(width+.5,.18,depth+.5))
        for n in Node.all:
            if n.name==old+' drain':n.pos[1]=1.8;n.scale[1]=3.6
        front=cz-depth/2;back=cz+depth/2;gap=1.8;segment=(width-gap)/2
        group=Node(label,root)
        box_node(label+' floor',group,(cx,.015,cz),(width,.15,depth),'M_Floor')
        box_node(label+' back wall',group,(cx,1.8,back),(width,3.6,.20),'M_Plaster')
        for side in [-1,1]:
            box_node(label+' side wall',group,(cx+side*width/2,1.8,cz),(.20,3.6,depth),'M_Brick')
            box_node(label+' entry wall',group,(cx+side*(gap/2+segment/2),1.8,front),(segment,3.6,.20),'M_Brick')
        box_node(label+' entry lintel',group,(cx,3.03,front),(gap,1.14,.20),'M_Brick')
        plaque(label+' entrance sign',(cx,2.9,front-.16),label.upper(),(3.3,.53))
        for dx in [-width*.25,width*.25]:
            box_node(label+' fluorescent',group,(cx+dx,3.5,cz),(.25,.08,1.7),'M_Lamp',False)
            light(lights,label+' ceiling light',(cx+dx,3.2,cz),5,9,(.97,.95,.87))
        return group
    canteen=room('Laundry','Inmate canteen',31,32,12,8)
    for x in [28.1,33.9]:
        box_node('Mess table',canteen,(x,.77,32),(2.05,.12,1.10),'M_Metal')
        for z in [30.9,33.1]:
            box_node('Mess bench',canteen,(x,.44,z),(2.05,.09,.38),'M_Wood')
            for dx in [-.7,.7]:box_node('Mess bench leg',canteen,(x+dx,.22,z),(.065,.44,.26),'M_Metal')
        box_node('Mess tray',canteen,(x,.86,32),(.43,.035,.30),'M_Chrome',False)
    box_node('Food service counter',canteen,(31,.90,35.2),(6.5,.18,.8),'M_Metal')
    box_node('Food counter base',canteen,(31,.41,35.2),(6.5,.82,.65),'M_WallPaint')
    for x in [28.8,31,33.2]:mesh_node('Meal serving pot',canteen,(x,1.12,35.2),(.48,.32,.48),'M_Chrome','PrisonCylinder',collision=False)
    plaque('Canteen schedule',(25.14,1.9,32.8),'MESS HALL\n06:30 / 12:00 / 18:00',(1.8,.75),(0,90,0))

    wash=room('Workshop annex','Inmate showers',36,17,9,7)
    for x in [33.1,35.0,36.9]:
        box_node('Shower partition',wash,(x-.82,1.05,19.1),(.07,2.1,2.3),'M_Ceramic')
        box_node('Shower pipe',wash,(x,1.45,20.27),(.045,2.55,.045),'M_Chrome',False)
        mesh_node('Shower head',wash,(x,2.63,20.04),(.19,.07,.22),'M_Chrome','PrisonSphere',collision=False)
        box_node('Shower valve',wash,(x,1.03,20.15),(.14,.11,.08),'M_Chrome',False)
        box_node('Shower drain',wash,(x,.105,19.20),(.24,.015,.24),'M_DarkMetal',False)
    for z in [15.1,16.6]:
        mesh_node('Washroom sink',wash,(39.95,.85,z),(.57,.22,.58),'M_Ceramic','PrisonSphere',collision=False)
        box_node('Washroom mirror',wash,(40.37,1.53,z),(.018,.66,.56),'M_Chrome',False)
        box_node('Sink faucet',wash,(40.18,1.04,z),(.06,.15,.08),'M_Chrome',False)
    box_node('Changing bench',wash,(33.9,.44,15.45),(2.8,.11,.48),'M_Wood')
    for x in [32.8,35]:box_node('Changing bench support',wash,(x,.22,15.45),(.12,.44,.32),'M_Metal')
    plaque('Shower rules',(31.66,1.85,17.3),'SHOWERS\nKEEP THE WALKWAY CLEAR',(1.9,.70),(0,90,0))

    # An open-front inmate workshop surrounds the existing mission contact.
    work=Node('Inmate workshop',root)
    for x in [10,16.4]:box_node('Workshop side',work,(x,1.8,32.6),(.17,3.6,5.6),'M_Plaster')
    box_node('Workshop back',work,(13.2,1.8,35.4),(6.4,3.6,.17),'M_Brick')
    box_node('Workshop shelter roof',work,(13.2,3.7,32.6),(6.7,.18,5.9),'M_DarkMetal')
    plaque('Inmate workshop sign',(13.2,3.18,29.7),'INMATE WORKSHOP',(3.9,.52))
    light(lights,'Workshop work light',(13.2,3.35,32.6),5,8,(1,.88,.69))
    for x in [11.1,15.35]:box_node('Workshop storage shelf',work,(x,1.1,34.55),(.95,2.0,.65),'M_WallPaint')

    # Security landmarks make the court read as a prison rather than a plaza.
    for z in [7,12.3]:box_node('Eastern checkpoint post',root,(18.2,1.55,z),(.20,3.1,.20),'M_Metal')
    box_node('Eastern checkpoint lintel',root,(18.2,3.12,9.65),(.20,.18,5.5),'M_Metal')
    plaque('Eastern checkpoint notice',(17.96,2.78,9.65),'VISITS / ISOLATION\nINMATE FACILITIES',(2.9,.58),(0,-90,0))
    plaque('Prison main identity',(0,5.40,4.18),'BLACKSTONE PENITENTIARY\nCELL BLOCKS B / C',(8.2,1.15),(0,0,0))
    plaque('Yard security rules',(-17.91,2.5,22),'INMATE RECREATION YARD\nNO ENTRY TO GUARD POSTS',(4.2,1.0),(0,90,0))
    plaque('Canteen direction',(23,1.55,26),'MESS HALL  →\nSHOWERS  →',(2.6,.8))
    # One shared helix mesh is reused on the three high courtyard walls.
    wire=Mesh();points=[]
    for i in range(721):
        x=-16+i/720*32;a=i/720*math.tau*64
        points.append((x,.17*math.cos(a),.17*math.sin(a)))
    wire.merge(tube(points,.009,5));save_mesh('PrisonRazorWire',wire,'Environment/PrisonFacilities')
    mesh_node('North prison razor wire',root,(0,4.83,40.3),(1,1,1),'M_Rust','PrisonRazorWire',collision=False)
    for x in [-18.2,18.2]:mesh_node('Side prison razor wire',root,(x,4.83,23),(1,1,1),'M_Rust','PrisonRazorWire',rot=(0,90,0),collision=False)
