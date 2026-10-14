"""Preview native supplied door/toilet geometry offline, not in Unity."""
from render_revision12_previews import native,mark
from render_current_previews import placed,cube
import render_supplied_previews as r


def main():
    out=r.ROOT/'Documentation/SolitaryPreviews';out.mkdir(exist_ok=True)
    for name,height,eye in [('SolitaryDoor',2.1,(2.5,1.8,3.5)),('PrisonToilet',.88,(1.4,1.05,1.8))]:
        scene=placed(native(name),height,(0,0,0))+[cube('Floor',(0,-.02,0),(5,.04,5),(.43,.46,.45,1))]
        image=r.render(scene,size=(1280,720),eye=eye,center=(0,height*.5,0))
        mark(image,'SUPPLIED '+name.upper()+' / FULL SOURCE MESH').save(out/(name+'.png'))
        print(name,flush=True)


if __name__=='__main__':main()
