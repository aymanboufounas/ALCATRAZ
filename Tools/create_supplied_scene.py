"""Create a compact native scene that loads the supplied exterior prefabs."""
from pathlib import Path
import re
import unity_writer as u
root=u.ROOT
source=(root/'Assets/Game/Scenes/SC_AlcatrazIsland.unity').read_text()
blocks={int(m[2]):b for b in re.split(r'(?=--- !u!)',source) if (m:=re.match(r'--- !u!(\d+) &(\d+)',b))}
u.Node.all=[];u.Node.counter=41000000
world=u.Node('Alcatraz supplied island',static=False)
world.script('Assets/Game/Supplied/Scripts/SuppliedIslandWorld.cs')
world.script('Assets/Game/Foundation/Scripts/FoundationBootstrap.cs','  storyMode: 0\n')
world.script('Assets/Game/Foundation/Scripts/FoundationHUD.cs','  worldTitle: "ALCATRAZ\\nISLAND"\n  storyScene: SC_AlcatrazChapter01\n')
world.script('Assets/Game/Alcatraz/Scripts/AlcatrazMap.cs','  suppliedLayout: 1\n')
world.script('Assets/Game/Alcatraz/Scripts/AlcatrazPresentation.cs')
player=u.Node('Player',pos=(-107,49.3,23),rot=(0,250,0),layer=8,static=False)
target=u.Node('CameraTarget',player,pos=(0,1.45,0),static=False)
def body(id):
 return blocks[id].split('  m_GameObject: ',1)[1].split('\n',1)[1]
player.component(143,body(8742))
player.script('Assets/_DesertShift/Scripts/Player/PlayerInputHandler.cs')
player.script('Assets/_DesertShift/Scripts/Player/PlayerMovement.cs',f'  cameraTarget: {{fileID: {target.tid}}}\n')
player.script('Assets/_DesertShift/Scripts/Interaction/PlayerInteractor.cs')
player.script('Assets/Game/Scripts/AI/PrisonActor.cs','  displayName: Elias Vale\n  driveLocomotion: 0\n')
camera=u.Node('Main Camera',pos=(-105,51,25),static=False)
camera.component(20,body(47222))
# Retain the camera's URP settings and the existing sunlight/volume settings.
if 47223 in blocks:camera.component(114,body(47223))
settings=''.join(b for b in blocks.values() if b.startswith(('--- !u!29 ','--- !u!104 ','--- !u!157 ','--- !u!196 ')))
text=u.HEAD+settings+''.join(u.node_yaml(n) for n in u.Node.all)
retained=[]
for goid in (47840,47860):
 go=blocks[goid];ids=[int(x) for x in re.findall(r'component: \{fileID: (\d+)\}',go)]
 text+=go+''.join(blocks[i] for i in ids);retained.append(ids[0])
text+='--- !u!1660057539 &9223372036854775807\nSceneRoots:\n  m_ObjectHideFlags: 0\n  m_Roots:\n'
for tid in [n.tid for n in u.Node.all if n.parent is None]+retained:text+=f'  - {{fileID: {tid}}}\n'
path='Assets/Game/Scenes/SC_AlcatrazSuppliedIsland.unity';u.write(path,'\n'.join(line.rstrip() for line in text.splitlines())+'\n');u.meta(path)
build=root/'ProjectSettings/EditorBuildSettings.asset';data=build.read_text()
entry=f'  - enabled: 1\n    path: {path}\n    guid: {u.guid(path)}\n'
if path not in data:build.write_text(data.replace('  m_Scenes:\n','  m_Scenes:\n'+entry))
for p in (root/'Assets/Game/Supplied/Scripts').rglob('*'):
 if p.suffix=='.cs':u.meta(str(p.relative_to(root)),'MonoImporter')
u.meta('Assets/Game/Supplied/Scripts','DefaultImporter')
print('Created compact supplied island scene:',len(text),'bytes')
