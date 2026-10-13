"""Source geometry previews of equipment fitting and glass, not Unity screenshots."""
import re
import numpy as np
import moderngl
from PIL import ImageDraw, ImageFont
import render_supplied_previews as r


def save(meshes, path, label, eye, center):
    r.C.enable(moderngl.BLEND)
    r.C.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
    meshes=sorted(meshes,key=lambda m:m['color'][3]<.99)
    image=r.render(meshes,size=(1280,720),eye=eye,center=center)
    draw=ImageDraw.Draw(image);draw.rectangle((0,0,1280,48),fill=(15,24,30))
    draw.text((20,15),label+' / OFFLINE SOURCE PREVIEW — NOT UNITY',
              font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16),fill=(230,224,210))
    image.save(path)


def main():
    out=r.ROOT/'Documentation/PoliceHelicopterPreviews';out.mkdir(parents=True,exist_ok=True)
    officer=r.fit(r.police(),1.82,(0,0,0))
    head=next(m for m in officer if m['name']=='policeman_head');lo,hi=r.bounds([head]);center=(lo+hi)/2
    reverse=np.diag([-1,1,-1,1])
    helmet=[r.transform(m,reverse) for m in r.gltf('Helmet')]
    vest=[r.transform(m,reverse) for m in r.gltf('Vest')]
    fitted=officer+r.fit(helmet,.32,(center[0],hi[1]-.065,center[2]),bottom=False)
    fitted+=r.fit(vest,.56,(center[0],1.27,center[2]-.025),bottom=False)
    save(fitted,out/'Police.png','SUPPLIED POLICE / HEAD-ALIGNED EQUIPMENT',(2,1.7,3),(0,.95,0))
    save(fitted,out/'PoliceRear.png','SUPPLIED POLICE / EQUIPMENT REAR',(-2,1.7,-3),(0,.95,0))
    helicopter=r.fit(r.gltf('Helicopter'),2.8,(0,0,0))
    mat=(r.RES/'Baked/Materials/Helicopter_0.mat').read_text()
    alpha=float(re.search(r'- _BaseColor: .*a: ([\d.]+)',mat)[1])
    for mesh in helicopter:
        if mesh['name']=='vidrio':mesh['color']=[*mesh['color'][:3],alpha]
    save(helicopter,out/'Helicopter.png','LITTLE BIRD / TRANSPARENT GLASS APPROXIMATION',(8,4,8),(0,1.3,0))
    print('Rendered police front/rear and helicopter source previews')


if __name__=='__main__':
    main()
