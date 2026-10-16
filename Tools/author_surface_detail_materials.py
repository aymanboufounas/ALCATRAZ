"""Author additive material profiles; preserve source atlas, models and colliders."""
from pathlib import Path
import re
import unity_writer as u

BASE='Assets/Game/Alcatraz/Resources/Alcatraz/SurfaceDetails'
SHADER='2c3ca6401f684c1caac06a2213adeb4c'

def reference(path,fid=2800000):
    meta=(u.ROOT/(path+'.meta')).read_text()
    return '{fileID: '+str(fid)+', guid: '+re.search(r'^guid: (\w+)',meta,re.M)[1]+', type: 3}'

def author():
    u.ART=BASE
    normal='Assets/Game/Textures/PBR_concrete_floor_worn_001_Normal.png'
    ground='Assets/Game/Textures/PBR_concrete_floor_worn_001_Base.png'
    surface='Assets/Game/Textures/PBR_concrete_floor_worn_001_Surface.png'
    # Standard URP profiles retain real CC0 albedo/normal/AO/smoothness maps.
    outputs=[]
    for name,stem in [('HelipadConcrete','concrete_floor_worn_001'),('DockTimber','wood_planks')]:
        prefix='Assets/Game/Textures/PBR_'+stem
        generated=u.material(name,(.86,.86,.84,1),rough=.82,texture=prefix+'_Base.png',normal=prefix+'_Normal.png',surface=prefix+'_Surface.png',occlusion=prefix+'_Surface.png',tiling=6)
        destination=BASE+'/'+name+'.mat'
        u.write(destination,(u.ROOT/generated).read_text())
        u.meta(destination,'NativeFormatImporter','  mainObjectFileID: 2100000\n')
        (u.ROOT/generated).unlink();Path(str(u.ROOT/generated)+'.meta').unlink()
        outputs.append(destination)
    temp=u.material('IslandSurface',(1,1,1,1),rough=.85,shader_guid=SHADER)
    source=(u.ROOT/temp).read_text()
    texture_rows=''
    for key,path in {
      '_GroundMap':ground,'_GroundNormal':normal,'_GroundSurface':surface,
      '_WallMap':'Assets/Game/Textures/PBR_brick_wall_001_Base.png',
      '_WallNormal':'Assets/Game/Textures/PBR_brick_wall_001_Normal.png',
      '_WallSurface':'Assets/Game/Textures/PBR_brick_wall_001_Surface.png'
    }.items():
        texture_rows+=f'    - {key}:\n        m_Texture: {reference(path)}\n        m_Scale: {{x: 1, y: 1}}\n        m_Offset: {{x: 0, y: 0}}\n'
    source=source.replace('    m_Ints: []\n',texture_rows+'    m_Ints: []\n')
    values={'_GroundAlbedoReplacement':.65,'_GroundWorldScale':.65,'_WallWorldScale':.5,'_DetailColorStrength':.22,'_DetailNormalStrength':.7,
      '_GroundSmoothness':.18,'_WallSmoothness':.12,'_TriplanarSharpness':4,'_GroundSlopeStart':.5,
      '_GroundSlopeEnd':.85,'_DetailFadeStart':45,'_DetailFadeEnd':120,'_SurfaceVariation':.35,'_DetailOcclusionStrength':.3}
    source=source.replace('    m_Colors:\n',''.join(f'    - {key}: {value}\n' for key,value in values.items())+'    m_Colors:\n')
    destination=BASE+'/IslandSurface.mat';u.write(destination,source);u.meta(destination,'NativeFormatImporter','  mainObjectFileID: 2100000\n')
    (u.ROOT/temp).unlink();Path(str(u.ROOT/temp)+'.meta').unlink();outputs.append(destination)
    temporary=u.ROOT/BASE/'Materials'
    if temporary.exists() and not any(temporary.iterdir()):temporary.rmdir()
    u.write(BASE+'.meta','fileFormatVersion: 2\nguid: '+u.guid(BASE)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
    for file in (u.ROOT/BASE).rglob('*'):
        if file.is_file():file.write_text('\n'.join(line.rstrip() for line in file.read_text().splitlines())+'\n')
    script='Assets/Game/Alcatraz/Scripts/AlcatrazEnvironmentDetails.cs'
    u.meta(script,'MonoImporter','  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n')
    meta=u.ROOT/(script+'.meta');meta.write_text('\n'.join(line.rstrip() for line in meta.read_text().splitlines())+'\n')
    print('Authored '+str(len(outputs))+' additive profiles with existing source-resolution PBR maps.')

if __name__=='__main__':author()
