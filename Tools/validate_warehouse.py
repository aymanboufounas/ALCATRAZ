"""Offline asset and doorway checks; not Unity compilation or swept physics."""
from pathlib import Path
import argparse,hashlib,json,re,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'Assets/Game/Supplied/Resources/AlcatrazExtras'
def attributes(path):
    s=path.read_text();v=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',s)[1]),'<f4').reshape(-1,12);t=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)',s)[1]),'<u4' if 'm_IndexFormat: 1' in s else '<u2').reshape(-1,3);return v,t
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archives',type=Path);args=parser.parse_args();checks=[]
    def check(ok,name):checks.append({'pass':bool(ok),'check':name})
    catalog=json.loads((BASE/'Catalog.json').read_text());entries={e['name']:e for e in catalog};check(len(catalog)==23 and len(entries)==23,'All 23 packs have distinct entries')
    source=(ROOT/'Assets/Game/Supplied/Scripts/SuppliedExtrasWorld.cs').read_text();placements=[(n,float(h),np.array([float(x.strip().rstrip('f')) for x in p.split(',')])) for n,h,p in re.findall(r'Model\("(Warehouse|AcidBarrel|ExplosiveBarrel)",([\d.]+)f?,new Vector3\(([^)]+)\)\)',source)];check(len(placements)==5,'One warehouse and four barrel instances');mesh_sets={}
    for n in ('Warehouse','AcidBarrel','ExplosiveBarrel'):
        e=entries[n];check(e==json.loads((BASE/n/'Source.json').read_text()),n+' catalog matches its source record')
        if args.archives:check(hashlib.sha256((args.archives/e['archive']).read_bytes()).hexdigest()==e['sha256'],n+' original archive hash')
        text=(BASE/n/(n+'.prefab')).read_text();guids=re.findall(r'MeshCollider:[\s\S]*?m_Mesh: \{fileID: \d+, guid: (\w+)',text);check(bool(guids),n+' has solid collision meshes');meshes={}
        for p in (BASE/n/'Meshes').glob('*.asset'):
            g=re.search(r'^guid: (\w+)',Path(str(p)+'.meta').read_text(),re.M)[1];v,t=attributes(p);meshes[p.stem]=(v[t,:3],g in guids)
        mesh_sets[n]=meshes
    floors=[]
    for p in (BASE/'Warehouse/Meshes').glob('Warehouse_M23_*.asset'):
        v,_=attributes(p);plane=np.c_[v[:,[0,2]],np.ones(len(v))];uv=np.linalg.lstsq(plane,v[:,10:12],rcond=None)[0];check(np.max(abs(plane@uv-v[:,10:12]))<1e-5,'Floor texture alignment: '+p.name)
    n,h,pos=next(p for p in placements if p[0]=='Warehouse');lo,hi=np.array(entries[n]['bounds']);scale=h/(hi[1]-lo[1]);center=np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2]);fitted={k:((t-center)*scale+pos,solid) for k,(t,solid) in mesh_sets[n].items()};verts=np.concatenate([t.reshape(-1,3) for t,_ in fitted.values()]);wl,wh=verts.min(0),verts.max(0);check(wl[0]>50 and wh[0]<95.5 and max(abs(wl[2]),abs(wh[2]))<24.5,'Warehouse fits its connected bay')
    solid=np.concatenate([t for t,enabled in fitted.values() if enabled]);lower,upper=solid.min(1),solid.max(1);doors=[]
    for key,(tri,_) in fitted.items():
        if not key.startswith(('Warehouse_M9_','Warehouse_M10_')):continue
        dc=(tri.min(axis=(0,1))+tri.max(axis=(0,1)))/2;spawn=np.array([dc[0]+1.3,pos[1]+.08,dc[2]]);floor=solid[(upper[:,1]<spawn[1]+.1)&(lower[:,1]>spawn[1]-.35)];a=floor[:,0][:,[0,2]];b=floor[:,1][:,[0,2]]-a;c=floor[:,2][:,[0,2]]-a;den=b[:,0]*c[:,1]-b[:,1]*c[:,0];supported=True
        for offset in ((0,0),(.22,0),(-.22,0),(0,.22),(0,-.22)):
            q=spawn[[0,2]]+offset-a;u=np.divide(q[:,0]*c[:,1]-q[:,1]*c[:,0],den,out=np.zeros(len(den)),where=abs(den)>1e-8);v=np.divide(b[:,0]*q[:,1]-b[:,1]*q[:,0],den,out=np.zeros(len(den)),where=abs(den)>1e-8);supported &= bool(np.any((abs(den)>1e-8)&(u>=-1e-4)&(v>=-1e-4)&(u+v<=1.0001)))
        obstruction=(lower[:,1]<spawn[1]+1.79)&(upper[:,1]>spawn[1]+.11)
        for axis in (0,2):obstruction &= (lower[:,axis]<spawn[axis]+.24)&(upper[:,axis]>spawn[axis]-.24)
        check(supported,key+' full foot support');check(not obstruction.any(),key+' standing clearance');doors.append({'door':key,'entry':spawn.tolist(),'supported':supported,'obstructed':bool(obstruction.any())})
    check(len(doors)==2,'Two door entry points');barrels=[]
    for n,h,pos in placements:
        if n=='Warehouse':continue
        lo,hi=np.array(entries[n]['bounds']);size=(hi-lo)*h/(hi[1]-lo[1]);lo=pos-size*np.array([.5,0,.5]);hi=lo+size;check(size[0]<.85 and size[2]<.85 and abs(size[1]-1.1)<1e-6,n+' fitted size');check(lo[2]>wh[2]+.5,n+' clear of warehouse')
        for ol,oh in barrels:check(np.any(hi<=ol) or np.any(lo>=oh),n+' clear of other barrels')
        barrels.append((lo,hi))
    result={'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':len(checks),'errors':[c['check'] for c in checks if not c['pass']],'doors':doors,'warehouse_bounds':[wl.tolist(),wh.tolist()],'scope':'Archive hashes, native meshes, UV alignment, fitted sizes, barrel separation, five-point floor support and conservative stationary clearance. Unity compilation, live contacts and swept collision remain unverified.'};(ROOT/'Validation/Revision12_WarehouseChecks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result['status']!='PASS'
if __name__=='__main__':sys.exit(main())
