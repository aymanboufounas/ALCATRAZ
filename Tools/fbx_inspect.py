"""Small read-only binary FBX inspector for source integrity and preview tooling."""
from dataclasses import dataclass
from pathlib import Path
from io import BytesIO
import struct, zlib
import numpy as np

@dataclass
class Node:
    name: str
    props: list
    children: list
    def child(self, name):
        return next((x for x in self.children if x.name == name), None)
    def array(self, name):
        node=self.child(name)
        return None if node is None else node.props[0]

def read(path):
    data=Path(path).read_bytes(); f=BytesIO(data)
    if f.read(23) != b'Kaydara FBX Binary  \x00\x1a\x00': raise ValueError('Not a binary FBX')
    version=struct.unpack('<I',f.read(4))[0]; wide=version>=7500
    nullsize=25 if wide else 13
    def prop():
        code=f.read(1).decode('ascii')
        scalar={'Y':('<h',2),'C':('<?',1),'I':('<i',4),'F':('<f',4),'D':('<d',8),'L':('<q',8)}
        if code in scalar:
            fmt,n=scalar[code];return struct.unpack(fmt,f.read(n))[0]
        if code in 'SR':
            length=struct.unpack('<I',f.read(4))[0];value=f.read(length)
            return value.decode('utf-8',errors='replace') if code=='S' else value
        if code in 'dfilbc':
            count,encoding,length=struct.unpack('<III',f.read(12));raw=f.read(length)
            if encoding==1:raw=zlib.decompress(raw)
            dtype={'d':'<f8','f':'<f4','i':'<i4','l':'<i8','b':'u1','c':'i1'}[code]
            expected=count*np.dtype(dtype).itemsize
            if len(raw)!=expected:raise ValueError('Damaged FBX array')
            return np.frombuffer(raw,dtype=dtype).copy()
        raise ValueError('Unknown FBX property '+code)
    def node():
        start=f.tell();header=f.read(nullsize)
        if len(header)!=nullsize:raise ValueError('Truncated FBX node')
        end,count,length,nlen=struct.unpack('<QQQB' if wide else '<IIIB',header)
        if end==0:return None
        name=f.read(nlen).decode('utf-8');pstart=f.tell()
        props=[prop() for _ in range(count)]
        if f.tell()!=pstart+length or end>len(data):raise ValueError('Invalid FBX node length')
        children=[]
        while f.tell()<end-nullsize:
            c=node()
            if c is None:break
            children.append(c)
        f.seek(end)
        return Node(name,props,children)
    nodes=[]
    while True:
        n=node()
        if n is None:break
        nodes.append(n)
    return Node('FBX',[version],nodes)

def summary(path):
    root=read(path);objects=root.child('Objects');result={'version':root.props[0]}
    if objects is None:return result
    meshes=[n for n in objects.children if n.name=='Geometry' and len(n.props)>2 and n.props[2]=='Mesh']
    result['control_points']=sum(len(n.array('Vertices'))//3 for n in meshes)
    result['polygons']=sum(np.sum(n.array('PolygonVertexIndex')<0).item() for n in meshes)
    result['bones']=[n.props[1].split('\x00')[0] for n in objects.children if n.name=='Model' and n.props[2]=='LimbNode']
    result['curves']=sum(n.name=='AnimationCurve' for n in objects.children)
    result['clusters']=sum(n.name=='Deformer' and n.props[2]=='Cluster' for n in objects.children)
    return result

if __name__=='__main__':
    import sys,json
    for p in sys.argv[1:]:print(json.dumps({'file':p,**summary(p)}))
