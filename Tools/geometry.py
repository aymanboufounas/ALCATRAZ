"""Original deterministic mesh authoring. Coordinates are Unity metres (Y up)."""
import math
import numpy as np
from scipy.spatial.transform import Rotation

class Mesh:
    def __init__(self):
        self.v=[]; self.n=[]; self.uv=[]; self.t=[]; self.weights=[]
    def tri(self,a,b,c,uvs=None,normals=None):
        pts=np.array([a,b,c],dtype=float)
        normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]); l=np.linalg.norm(normal)
        if l<1e-10:return
        normal/=l
        i=len(self.v);self.v.extend(pts.tolist());self.t.extend([i,i+1,i+2])
        self.n.extend(normals if normals is not None else [normal.tolist()]*3)
        self.uv.extend(uvs or [(0,0),(1,0),(1,1)])
    def quad(self,a,b,c,d,uv=None):
        uv=uv or [(0,0),(1,0),(1,1),(0,1)]
        self.tri(a,b,c,uv[:3]);self.tri(a,c,d,[uv[0],uv[2],uv[3]])
    def merge(self,other,pos=(0,0,0),scale=(1,1,1),rot=(0,0,0)):
        if not other.v:return self
        r=Rotation.from_euler('xyz',rot,degrees=True).as_matrix()
        v=np.array(other.v)*scale; n=np.array(other.n)/np.array(scale)
        n=n@r.T;n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-8)
        start=len(self.v); self.v.extend((v@r.T+pos).tolist());self.n.extend(n.tolist())
        self.uv.extend(other.uv);self.t.extend([x+start for x in other.t])
        return self

def box(size=(1,1,1),bevel=0.025):
    """Bevelled box with smooth chamfers and flat central faces."""
    out=Mesh(); half=np.array(size)/2; b=min(bevel,min(half)*.45)
    inner=half-b
    for axis in range(3):
      axes=[i for i in range(3) if i!=axis]
      for sign in [-1,1]:
        us=[-half[axes[0]],-inner[axes[0]],inner[axes[0]],half[axes[0]]]
        vs=[-half[axes[1]],-inner[axes[1]],inner[axes[1]],half[axes[1]]]
        def point(u,v):
            p=np.zeros(3);p[axis]=sign*half[axis];p[axes[0]]=u;p[axes[1]]=v
            c=np.minimum(np.maximum(p,-inner),inner);n=p-c;n/=np.linalg.norm(n)
            return c+n*b,n
        for i in range(3):
          for j in range(3):
            ps=[point(us[i],vs[j]),point(us[i+1],vs[j]),point(us[i+1],vs[j+1]),point(us[i],vs[j+1])]
            ids=[0,1,2,3]
            if np.dot(np.cross(ps[1][0]-ps[0][0],ps[2][0]-ps[0][0]),ps[0][1])<0:ids=[3,2,1,0]
            for a,c,d in [(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])]:
                out.tri(ps[a][0],ps[c][0],ps[d][0],[(ps[k][0][axes[0]],ps[k][0][axes[1]]) for k in [a,c,d]],[ps[k][1].tolist() for k in [a,c,d]])
    return out

def ellipsoid(size=(1,1,1),rings=14,segments=24,seed=None):
    m=Mesh(); rng=np.random.default_rng(seed or 0)
    def p(i,j):
        a=math.pi*i/rings;b=2*math.pi*j/segments
        x=np.array([math.sin(a)*math.cos(b),math.cos(a),math.sin(a)*math.sin(b)])
        fac=1
        if seed is not None:fac=1+.13*math.sin(b*3+a*4+seed)+.055*math.cos(b*7-a*3)
        return x*np.array(size)*.5*fac
    for i in range(rings):
      for j in range(segments):
        for ids in [[(i,j),(i+1,j+1),(i+1,j)],[(i,j),(i,j+1),(i+1,j+1)]]:
          ps=[p(*x) for x in ids]
          ns=[q/(np.array(size)**2) for q in ps];ns=[(q/np.linalg.norm(q)).tolist() for q in ns]
          m.tri(*ps,uvs=[(b/segments,a/rings) for a,b in ids],normals=ns)
    return m

def cylinder(radius=.5,height=1,segments=24,top_radius=None):
    top_radius=radius if top_radius is None else top_radius
    m=Mesh()
    for j in range(segments):
        a=j*math.tau/segments;b=(j+1)*math.tau/segments
        p=[(radius*math.cos(a),-height/2,radius*math.sin(a)),(top_radius*math.cos(a),height/2,top_radius*math.sin(a)),(top_radius*math.cos(b),height/2,top_radius*math.sin(b)),(radius*math.cos(b),-height/2,radius*math.sin(b))]
        for ids in [(0,1,2),(0,2,3)]:
            ns=[]
            for k in ids:
                angle=a if k in [0,1] else b
                n=np.array([math.cos(angle),(radius-top_radius)/height,math.sin(angle)]);n/=np.linalg.norm(n);ns.append(n.tolist())
            m.tri(*(p[k] for k in ids),normals=ns)
        m.tri((0,height/2,0),p[2],p[1]);m.tri((0,-height/2,0),p[0],p[3])
    return m

def tube(points,radius=.035,sides=10):
    m=Mesh();ps=np.array(points);frames=[]
    for i,p in enumerate(ps):
        d=ps[min(i+1,len(ps)-1)]-ps[max(0,i-1)];d=d/max(np.linalg.norm(d),1e-8)
        q=np.array([0,1,0]) if abs(d[1])<.9 else np.array([1,0,0])
        a=np.cross(d,q);a/=np.linalg.norm(a);b=np.cross(d,a)
        frames.append([(p+radius*(math.cos(j*math.tau/sides)*a+math.sin(j*math.tau/sides)*b)).tolist() for j in range(sides)])
    for i in range(len(ps)-1):
      for j in range(sides):
        k=(j+1)%sides;m.quad(frames[i][j],frames[i][k],frames[i+1][k],frames[i+1][j])
    return m

def torus(major=.4,minor=.1,segments=32,sides=12,arc=math.tau):
    ps=[(major*math.cos(arc*i/segments),0,major*math.sin(arc*i/segments)) for i in range(segments+1)]
    return tube(ps,minor,sides)

def lathe(profile,segments=32):
    m=Mesh()
    for i in range(len(profile)-1):
      y,r=profile[i];y2,r2=profile[i+1]
      for j in range(segments):
        a=math.tau*j/segments;b=math.tau*(j+1)/segments
        m.quad((r*math.cos(a),y,r*math.sin(a)),(r2*math.cos(a),y2,r2*math.sin(a)),(r2*math.cos(b),y2,r2*math.sin(b)),(r*math.cos(b),y,r*math.sin(b)))
    return m

def plane(w=1,d=1):
    m=Mesh();m.quad((-w/2,0,d/2),(w/2,0,d/2),(w/2,0,-d/2),(-w/2,0,-d/2));return m

def terrain_height(x,z):
    broad=1.8*np.sin(x*.017)*np.cos(z*.022)+.65*np.sin(x*.071+z*.045)+.28*np.cos(x*.18-z*.1)
    edge=np.clip((np.maximum(np.abs(x),np.abs(z))-205)/95,0,1)
    broad+=edge**2*(17+7*np.sin(x*.032+z*.013))
    camp=np.exp(-(((x+77)/18)**8+((z+18)/16)**8))
    wash=np.exp(-(((x-92)/33)**10+((z+16)/30)**10))
    driveway=np.exp(-(((x-89)/7)**12+((z+43)/18)**12))
    road=np.exp(-((z-road_z(x))/12)**4)
    flatten=np.maximum(np.maximum(np.maximum(camp,wash),road),driveway)
    return broad*(1-flatten)

def road_z(x):return -58+8*np.sin(np.asarray(x)*.0105)

def terrain_tile(x0,z0,size=100,step=4):
    m=Mesh();n=int(size/step)
    for j in range(n+1):
      for i in range(n+1):
        x=x0+i*step;z=z0+j*step;y=float(terrain_height(x,z))
        dx=float(terrain_height(x+.1,z)-terrain_height(x-.1,z))/.2
        dz=float(terrain_height(x,z+.1)-terrain_height(x,z-.1))/.2
        norm=np.array([-dx,1,-dz]);norm/=np.linalg.norm(norm)
        m.v.append([x,y,z]);m.n.append(norm.tolist());m.uv.append([(x+300)/600,(z+300)/600])
    for j in range(n):
      for i in range(n):
        a=j*(n+1)+i;b=a+1;c=a+n+1;d=c+1;m.t.extend([a,c,b,b,c,d])
    return m
