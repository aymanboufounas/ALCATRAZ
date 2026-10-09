"""Retarget CC0 MakeHuman anatomy to the chapter's articulated prisoner rig.
Only clothed characters' heads, necks and hands enter the game meshes.
See Documentation/ThirdParty_Art_Credits.md for source credits.
"""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from geometry import Mesh, ellipsoid
from unity_writer import ROOT

SOURCE=ROOT/'Tools/ArtSources'
_source=None
def load_source(ethnicity):
    global _source
    if _source is None:
        vertices=[];uv=[];faces=[];group=''
        for line in (SOURCE/'mh_base.obj').read_text().splitlines():
            if line.startswith('v '):vertices.append([float(x) for x in line[2:].split()])
            elif line.startswith('vt '):uv.append([float(x) for x in line[3:].split()][:2])
            elif line.startswith('g '):group=line[2:]
            elif line.startswith('f '):
                pairs=[tuple(int(q)-1 for q in x.split('/')[:2]) for x in line[2:].split()]
                for i in range(1,len(pairs)-1):faces.append((group,[pairs[0],pairs[i],pairs[i+1]]))
        _source=(np.array(vertices),np.array(uv),faces)
    v,uv,faces=_source;v=v.copy()
    for line in (SOURCE/(ethnicity+'-male-young.target')).read_text().splitlines():
        if not line or line.startswith('#'):continue
        fields=line.split()
        if len(fields)==4:v[int(fields[0])]+=np.array([float(x) for x in fields[1:]])
    return v,uv,faces

def mesh_from_faces(v,uv,faces,transform,weights,mirrored=False):
    # Topological smoothing respects UV seams and preserves facial loops.
    selected=[list(reversed(f)) if mirrored else f for group,f in faces];indices=np.array([[p[0] for p in f] for f in selected])
    out=Mesh()
    if not len(indices):return out
    p=transform(v);normal=np.zeros_like(p)
    face=np.cross(p[indices[:,1]]-p[indices[:,0]],p[indices[:,2]]-p[indices[:,0]])
    for i in range(3):np.add.at(normal,indices[:,i],face)
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
    for f in selected:
        ids=[p[0] for p in f];before=len(out.v)
        out.tri(*p[ids],uvs=[uv[x[1]].tolist() for x in f],normals=normal[ids].tolist())
        if len(out.v)>before:out.weights.extend(weights(p[i]) for i in ids)
    return out

def filter_original(mesh,predicate):
    out=Mesh();vertices=np.array(mesh.v)
    for a in range(0,len(mesh.t),3):
        ids=mesh.t[a:a+3];centre=np.mean(vertices[ids],axis=0)
        if not predicate(centre):continue
        start=len(out.v)
        for index in ids:
            out.v.append(mesh.v[index]);out.n.append(mesh.n[index]);out.uv.append(mesh.uv[index]);out.weights.append(mesh.weights[index])
        out.t.extend([start,start+1,start+2])
    return out

def improve(groups,profile,profiles,bones):
    w,belly,skin,cloth,cut,beard,face,height=profiles[profile]
    # Remove the earlier assembled face/hands/hair, retaining the clothed body.
    for key in ['M_EyeWhite','M_Iris','M_Pupil','M_SkinCrease','M_Lips','M_MouthLine','M_Hair','M_GreyHair','M_Nails','M_Beard'+skin,'M_Stubble'+skin]:groups.pop(key,None)
    # Rebuild the exposed forearms with an exact, tapered end. Centroid-cut
    # triangles from the former palm and forearm left jagged overlapping edges.
    from prison_character import loft
    forearms=Mesh();aw=min(w,1.15)
    bare=loft([(.205,.055*aw,.054*aw,0,0),(.28,.054*aw,.051*aw,0,0),(.38,.045*aw,.041*aw,0,0),(.46,.027,.027,0,0),(.509,.019,.020,0,0)],30)
    for side,sign in [('Left',-1),('Right',1)]:
        start=len(forearms.v);forearms.merge(bare,(sign*.22,1.43,0),rot=(0,0,-sign*90))
        for p in forearms.v[start:]:
            t=float(np.clip((abs(p[0])-.43)/.10,0,1))
            forearms.weights.append([bones[side+'UpperArm'],bones[side+'LowerArm'],1-t,t])
    groups['M_Skin'+skin]=forearms
    ethnicity='african' if skin in ['Deep','Brown'] else 'caucasian'
    v,uv,faces=load_source(ethnicity)
    def joint(name):
        ids=list({i for g,f in faces if g==name for i,_ in f})
        return np.mean(v[ids],axis=0)
    neck=joint('joint-neck');eye_height=joint('joint-l-eye')[1]
    body_ids=list({i for g,f in faces if g=='body' for i,_ in f})
    top=max(v[body_ids,1]);vertical_scale=.290/(top-neck[1])
    head_faces=[(g,f) for g,f in faces if g=='body' and all(v[i][1]>neck[1]-.62 for i,_ in f)]
    def head_transform(vertices):
        p=vertices.copy();p[:,0]*=.108*(1+(face%3-1)*.045)
        p[:,1]=1.50+(vertices[:,1]-neck[1])*vertical_scale
        p[:,2]*=.103
        # Distinct jaw/cheek silhouettes without changing UV topology.
        jaw=np.exp(-((p[:,1]-1.57)/.045)**2)
        p[:,0]*=1+jaw*(.10 if profile in ['Malik','Rival','Athletic'] else -.035 if profile=='Lean' else .02)
        # The source shoulder taper is wider than the existing shirt opening.
        # Ease only the lower neck inside the collar and extend its hidden edge
        # below the cloth, preserving the facial shape above the neck.
        blend=np.clip((1.525-p[:,1])/.033,0,1)
        blend=blend*blend*(3-2*blend)
        radius=np.maximum(np.sqrt((p[:,0]/.045)**2+((p[:,2]-.010)/.041)**2),1)
        p[:,0]=p[:,0]*(1-blend)+p[:,0]/radius*blend
        p[:,2]=p[:,2]*(1-blend)+(.010+(p[:,2]-.010)/radius)*blend
        return p
    def head_weights(p):
        if p[1]<1.545:
            t=float(np.clip((p[1]-1.485)/.06,0,1));return [bones['Neck'],bones['Head'],1-t,t]
        if p[1]<1.61 and p[2]>.04:
            t=float(np.clip((1.61-p[1])/.045,0,.75));return [bones['Jaw'],bones['Head'],t,1-t]
        return [bones['Head'],bones['Head'],1,0]
    groups['M_RealHead'+skin]=mesh_from_faces(v,uv,head_faces,head_transform,head_weights)
    # Scalp surfaces follow the authored cranial shape rather than a separate cap.
    if cut!='bald':
        threshold=eye_height+(.86 if cut=='receding' else .67 if cut=='buzz' else .53)
        eye_depth=joint('joint-l-eye')[2]
        hair_faces=[(g,f) for g,f in head_faces if all(v[i][1]>threshold+max(v[i][2]-eye_depth*.45,0)*.20 for i,_ in f)]
        hair=mesh_from_faces(v,uv,hair_faces,head_transform,lambda p:[bones['Head'],bones['Head'],1,0])
        for i in range(len(hair.v)):hair.v[i]=(np.array(hair.v[i])+np.array(hair.n[i])*(.0015 if cut=='buzz' else .0035)).tolist()
        groups['M_RealHairGrey' if profile=='Lean' else 'M_RealHair']=hair
    # Small anatomically positioned eyeballs remain behind the imported eyelids.
    head_pos=head_transform(v)
    for side,sign in [('Left',-1),('Right',1)]:
        eye_faces=[(g,f) for g,f in faces if g=='joint-'+('l' if sign<0 else 'r')+'-eye']
        ids=list({i for _,f in eye_faces for i,_ in f});centre=np.mean(head_pos[ids],axis=0)
        def add(mat,mesh,pos):
            m=groups.setdefault(mat,Mesh());count=len(m.v);m.merge(mesh,pos)
            m.weights.extend([[bones['Head'],bones['Head'],1,0] for _ in range(len(m.v)-count)])
        add('M_EyeWhite',ellipsoid((.028,.027,.027),14,24),centre)
        add('M_RealIris',ellipsoid((.010,.010,.0018),12,24),centre+np.array([0,0,.0137]))
        add('M_Pupil',ellipsoid((.004,.004,.001),10,20),centre+np.array([0,0,.0148]))
        add('M_EyeWhite',ellipsoid((.0012,.0012,.001),6,8),centre+np.array([-.002,.003,.0154]))
    # Retarget each detailed hand to the straight-arm bind pose. Fingers share
    # the hand bone; the current gameplay rig does not have finger animation.
    for side,source_sign,target_sign in [('Left',1,-1),('Right',-1,1)]:
        direction=np.array([source_sign*.50,-.65,1.18]);direction/=np.linalg.norm(direction)
        wrist=joint('joint-'+('l' if source_sign>0 else 'r')+'-hand')-direction*.20
        hand_faces=[(g,f) for g,f in faces if g=='body' and all(np.dot(v[i]-wrist,direction)>-.23 and np.linalg.norm(v[i]-wrist)<2.65 for i,_ in f)]
        up=np.array([0.,1.,0.]);up-=direction*np.dot(up,direction);up/=np.linalg.norm(up)
        depth=np.cross(direction,up)
        def hand_transform(vertices):
            q=vertices-wrist
            return np.stack([target_sign*(.716+q@direction*.091),1.43+q@up*.091,q@depth*.091],axis=1)
        def hand_weights(p):
            t=float(np.clip((abs(p[0])-.697)/.035,0,1))
            return [bones[side+'LowerArm'],bones[side+'Hand'],1-t,t]
        m=mesh_from_faces(v,uv,hand_faces,hand_transform,hand_weights,target_sign<0)
        target=groups.setdefault('M_RealHead'+skin,Mesh());start=len(target.v)
        target.v.extend(m.v);target.n.extend(m.n);target.uv.extend(m.uv);target.weights.extend(m.weights);target.t.extend([i+start for i in m.t])
    # Small cloth folds break the previous perfectly cylindrical silhouette.
    trousers='M_PrisonOrangeTrousers' if profile=='Elias' else 'M_Trousers'
    for name in ['M_'+cloth,trousers]:
        m=groups.get(name)
        if m is None:continue
        for i,p in enumerate(m.v):
            x,y,z=p;normal=np.array(m.n[i])
            amplitude=.0018*(np.sin(y*86+x*23)*np.sin(z*33+y*21))
            if name==trousers:amplitude*=(1+np.exp(-((y-.5)/.12)**2)*1.8)*np.clip((.95-y)/.035,0,1)
            else:amplitude*=np.clip((y-.975)/.04,0,1)
            m.v[i]=(np.array(p)+normal*amplitude).tolist()
    return {k:v for k,v in groups.items() if v.v}
