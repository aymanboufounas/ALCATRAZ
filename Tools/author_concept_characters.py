"""Author the concept materials without changing the shared Rocketbox source art."""
import unity_writer as uw

BASE = 'Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_16/'
uw.ART = BASE.rstrip('/')
head = uw.material('m019_head_elias08', [1, 1, 1, 1], .70,
                   texture=BASE + 'm019_head_elias08.png', normal=BASE + 'm019_head_normal.png')
body = uw.material('m019_body_elias08', [.74, .78, .72, 1], .80,
                   texture=BASE + 'm019_body_alcatraz.png', normal=BASE + 'm019_body_normal.png')
# Character Resources.Load paths sit beside the FBX, not in a Materials subfolder.
for path in [head, body]:
    target = BASE + path.rsplit('/', 1)[-1]
    uw.write(target, (uw.ROOT / path).read_text())
    uw.meta(target, 'NativeFormatImporter', '  mainObjectFileID: 2100000\n')
    (uw.ROOT / path).unlink()
    (uw.ROOT / (path + '.meta')).unlink()
BASE = 'Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_07/'
uw.ART = BASE.rstrip('/')
head = uw.material('m013_head_harrow08', [1, 1, 1, 1], .72,
                   texture=BASE + 'm013_head_harrow08.png', normal=BASE + 'm013_head_normal.png')
body = uw.material('m013_body_harrow08', [.93, .96, 1, 1], .82,
                   texture=BASE + 'm013_body_harrow.png', normal=BASE + 'm013_body_normal.png')
for path in [head, body]:
    target = BASE + path.rsplit('/', 1)[-1]
    uw.write(target, (uw.ROOT / path).read_text())
    uw.meta(target, 'NativeFormatImporter', '  mainObjectFileID: 2100000\n')
    (uw.ROOT / path).unlink()
    (uw.ROOT / (path + '.meta')).unlink()
print('Authored Elias and Harrow concept head/workwear materials')
