"""Check source detail, police texture bindings and helicopter glass; not gameplay."""
import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Assets/Game/Supplied/Resources/AlcatrazSupplied'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path);args=parser.parse_args()
    checks=[]
    def check(ok,label):checks.append({'pass':bool(ok),'check':label})
    def native_triangles(name):
        total=0
        for p in (BASE/'Baked/Meshes').glob(name+'_*.asset'):
            text=p.read_text();buffer=re.search(r'm_IndexBuffer: ([0-9a-f]+)',text)[1]
            width=4 if 'm_IndexFormat: 1' in text else 2;total+=len(buffer)//(2*width*3)
        return total
    police_source=sum(len(line.split())-3 for line in (BASE/'Police/Police.obj').read_text().splitlines() if line.startswith('f '))
    check(police_source>0 and native_triangles('Police')==police_source,'All source police triangles retained')
    prefab=(BASE/'Baked/Police.prefab').read_text()
    for i,part in enumerate(('body','gun','head')):
        path=BASE/'Police'/('policeman_'+part+'_d.jpg')
        guid=re.search(r'^guid: (\w+)',Path(str(path)+'.meta').read_text(),re.M)[1]
        mat=(BASE/'Baked/Materials'/('Police_'+str(i)+'.mat')).read_text()
        check('guid: '+guid in mat,'Supplied police '+part+' texture is bound')
        check('m_Name: "policeman_'+part+'"' in prefab,'Native police '+part+' renderer can be found')
    source=json.loads((BASE/'Helicopter/Helicopter.gltf').read_text())
    triangles=sum(source['accessors'][p['indices']]['count']//3 for node in source['nodes'] if 'mesh' in node for p in source['meshes'][node['mesh']]['primitives'])
    check(triangles>0 and native_triangles('Helicopter')==triangles,'All source helicopter triangles retained')
    glass_source=next(m for m in source['materials'] if m['name']=='vidrio')
    check(glass_source['extensions']['KHR_materials_transmission']['transmissionFactor']==1,'Source cockpit is transmissive glass')
    glass=(BASE/'Baked/Materials/Helicopter_0.mat').read_text()
    for key,value in (('_Surface',1),('_Blend',1),('_DstBlend',10),('_ZWrite',0),('_Cull',0)):
        check(re.search(r'- '+key+r': '+str(value)+r'\s',glass) is not None,'Glass setting '+key)
    check('m_CustomRenderQueue: 3000' in glass and 'RenderType: Transparent' in glass,'Glass uses the transparent render queue')
    check('_SURFACE_TYPE_TRANSPARENT' in glass and '_ALPHAPREMULTIPLY_ON' in glass,'Glass shader transparency keywords are enabled')
    alpha=float(re.search(r'- _BaseColor: .*a: ([\d.]+)',glass)[1]);check(0<alpha<.5,'Glass alpha reveals the cockpit')
    result={'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':len(checks),'errors':[c['check'] for c in checks if not c['pass']],
            'police_triangles':police_source,'helicopter_triangles':triangles,
            'scope':'Native source triangle counts, police texture/renderer references and URP glass settings. Equipment fitting is reviewed in offline previews; Unity rendering and flight physics are unverified.'}
    if args.report:args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result['status']!='PASS'


if __name__=='__main__':
    raise SystemExit(main())
