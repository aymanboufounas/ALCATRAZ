"""Use native FBX bones/curves to validate forward gait and orientation correction.
This checks source geometry and the yaw math; Unity import/playback needs Unity.
"""
from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation
from fbx_pose import Character, animation

ROOT=Path(__file__).resolve().parents[1]

def anatomical(world):
    vector=sum((world[f'Bip01 {side} Toe0'][:3,3]-world[f'Bip01 {side} Foot'][:3,3] for side in 'LR'))
    vector[1]=0
    return vector/np.linalg.norm(vector)

def main():
    checks=0
    for path in sorted((ROOT/'Assets/Game/Resources/BlackstoneFoundation/Characters').glob('*/*.fbx')):
        character=Character(path)
        source=anatomical(character.rig.sample())
        assert source[2]>.99, (path,'bind pose forward')
        for conversion in [np.diag([-1,1,1]),np.diag([1,1,-1])]:
            for parent in range(0,360,45):
                target=Rotation.from_euler('y',parent,degrees=True).apply([0,0,1])
                for imported_yaw in range(0,360,45):
                    forward=Rotation.from_euler('y',parent+imported_yaw,degrees=True).apply(conversion@source)
                    delta=np.arctan2(target[0],target[2])-np.arctan2(forward[0],forward[2])
                    corrected=Rotation.from_euler('y',delta).apply(forward)
                    assert np.dot(corrected,target)>.999999, (path,parent,imported_yaw)
                    checks+=1
    curves=[]
    for name in ['WalkSlow','Walk','WalkFast','Run','RunFast']:
        rig=animation(ROOT/f'Assets/Game/Foundation/Animations/Rocketbox/{name}.fbx')
        start,end=rig.sample(0,False),rig.sample(rig.duration,False)
        travel=end['Bip01'][:3,3]-start['Bip01'][:3,3]
        assert travel[2]>100 and abs(travel[0])<.1, (name,'source clip travels forward')
        # In-place stance must carry the planted foot backward across the body.
        times=np.linspace(0,rig.duration,121)
        feet=np.array([[rig.sample(t)[f'Bip01 {s} Foot'][:3,3] for s in 'LR'] for t in times])
        velocity=np.diff(feet,axis=0)/(times[1]-times[0])
        low=(feet[:-1,:,1]<np.quantile(feet[:,:,1],.4))
        stance=float(np.median(velocity[:,:,2][low]))
        assert stance<0, (name,'plant foot moves in the wrong direction',stance)
        checks+=2
        curves.append({'clip':name,'forward_travel_cm':float(travel[2]),'median_stance_z_cm_s':stance})
    result={'status':'PASS','checks':checks,'clips':curves,
            'scope':'FBX source anatomy, forward gait, and orientation math under both reflection conventions; Unity playback unverified'}
    (ROOT/'Validation/Revision11_CharacterForward.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
