"""Restore two reduced textures from committed original archives, byte for byte.

No mesh import, simplification, image resizing, texture re-encoding, material
rewrite or collision changes occur. --check is read-only and verifies exact
source bytes, preserved texture GUIDs, import settings and protected native files.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = 'Assets/Game/Supplied/Resources/AlcatrazExtras'
ARCHIVES = 'Documentation/SourceArchives'
CONFIG = [
    {'pack': 'PokerProps', 'archive': 'poker-set (1).zip',
     'archive_sha256': 'bdc5f0dee1dd28a0a6d845abdedcc925b7481f056858e1f9cd1015082a42bfd9',
     'member': 'textures/playing_cards.png',
     'texture_sha256': '573e2df682d5504db3d0d38b4ad6a5daee589166efc7cc872f89f38260dbd689',
     'source_dimensions': [6500, 2904], 'previous_dimensions': [2048, 915],
     'previous_name': 'T1.jpg', 'output_name': 'T1.png',
     'previous_sha256': 'e7cfdcf664764af2fd8eb8f48998fbb71d665bd1f12ea47fbba0165d53ba332d',
     'previous_bytes': 516127, 'guid': 'd25895a0ba442abc7360f914d9c94b39',
     'max_texture_size': 8192, 'protected_files': 83,
     'protected_sha256': '1d8771bdb803fbe42ca26267c9fb5b2c29286e866b3f4b67278a03db1a238793'},
    {'pack': 'Workshop', 'archive': 'alchemists-workshop-stylized-fantasy-scene.zip',
     'archive_sha256': 'd02bc1145249f1f03b8d899211736017f2408cebbc855aeea972e26f3b76bbff',
     'member': 'textures/TABLE_TEXTURE_111.png',
     'texture_sha256': '6168297d76391bb0e56d59890d4ace13b635eb560bc94e245f0b41b69a1093fe',
     'source_dimensions': [4096, 4096], 'previous_dimensions': [2048, 2048],
     'previous_name': 'T2.png', 'output_name': 'T2.png',
     'previous_sha256': '539f2a1584f184c97d543f26d2f8c9cb7b548efad6d10f0919475b1cf35e80e1',
     'previous_bytes': 402993, 'guid': '4c0450939cd2c402ecae9b8e30d54c75',
     'max_texture_size': 4096, 'protected_files': 73,
     'protected_sha256': '27187e2db4fa0a3742bf1ebd23d479e8967730ef71422de4598d2a8496ab9022'},
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def guid(path):
    return hashlib.md5(('DesertShift-2026/'+path).encode()).hexdigest()


def texture_meta(config):
    # nPOTScale=0 preserves the genuine 6500x2904 atlas dimensions. Streaming
    # mips are enabled; the shared graphics budget still controls residency.
    return f'''fileFormatVersion: 2
guid: {config['guid']}
TextureImporter:
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 1
    sRGBTexture: 1
  streamingMipmaps: 1
  streamingMipmapsPriority: 0
  nPOTScale: 0
  textureType: 0
  textureShape: 1
  maxTextureSize: {config['max_texture_size']}
  textureCompression: 2
  isReadable: 0
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 8
    wrapU: 0
    wrapV: 0
    wrapW: 0
  alphaSource: 1
  alphaIsTransparency: 0
  userData:
  assetBundleName:
  assetBundleVariant:
'''.encode()


def text_meta(path):
    return f'''fileFormatVersion: 2
guid: {guid(path)}
TextScriptImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
'''.encode()


def protected_native(config):
    folder = ROOT/BASE/config['pack']
    excluded = {'Textures/'+name+suffix
                for name in [config['previous_name'], config['output_name']]
                for suffix in ['', '.meta']}
    excluded.update(['QualityRestoration.json', 'QualityRestoration.json.meta'])
    hashes = {p.relative_to(folder).as_posix(): digest(p.read_bytes())
              for p in sorted(folder.rglob('*'))
              if p.is_file() and p.relative_to(folder).as_posix() not in excluded}
    inventory = digest(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode())
    assert len(hashes) == config['protected_files'], config['pack']+': native inventory changed'
    assert inventory == config['protected_sha256'], config['pack']+': protected native bytes changed'
    return hashes


def expected_outputs():
    outputs, reports, retired = {}, [], []
    catalog = json.loads((ROOT/BASE/'Catalog.json').read_text())
    entries = {entry['name']: entry for entry in catalog}
    for config in CONFIG:
        folder = BASE+'/'+config['pack']
        archive_path = ARCHIVES+'/'+config['archive']
        archive = ROOT/archive_path
        assert archive.is_file(), 'Required committed source archive missing: '+archive_path
        assert digest(archive.read_bytes()) == config['archive_sha256'], 'Source archive checksum changed'
        with zipfile.ZipFile(archive) as source:
            # Read one explicitly named regular member into memory. No archive
            # extraction, arbitrary member paths, scripts or source models run.
            info = source.getinfo(config['member'])
            assert not info.is_dir() and 0 < info.file_size < 32*1024*1024
            payload = source.read(info)
        assert digest(payload) == config['texture_sha256'], 'Source texture checksum changed'
        with Image.open(BytesIO(payload)) as image:
            assert image.format == 'PNG' and list(image.size) == config['source_dimensions']
            image.verify()
        assert config['max_texture_size'] >= max(config['source_dimensions'])
        source_entry = json.loads((ROOT/folder/'Source.json').read_text())
        assert source_entry == entries[config['pack']], 'Catalog and per-pack provenance differ'
        assert source_entry['sha256'] == config['archive_sha256']
        protected = protected_native(config)
        references = []
        for material in sorted((ROOT/folder/'Materials').glob('*.mat')):
            if config['guid'] in material.read_text():
                references.append(str(material.relative_to(ROOT)))
        assert references, 'Restored texture is not bound to an existing material'
        output_path = folder+'/Textures/'+config['output_name']
        previous_path = folder+'/Textures/'+config['previous_name']
        # Before first restoration, validate the exact known reduced input and
        # original GUID. Afterward, the source-exact output replaces that input.
        current = ROOT/previous_path
        if current.is_file() and digest(current.read_bytes()) != config['texture_sha256']:
            assert digest(current.read_bytes()) == config['previous_sha256'], 'Unexpected prior texture bytes'
            metadata = Path(str(current)+'.meta').read_text()
            assert re.search(r'^guid: ([a-f0-9]{32})$', metadata, re.M)[1] == config['guid']
        outputs[output_path] = payload
        outputs[output_path+'.meta'] = texture_meta(config)
        if previous_path != output_path:
            retired.extend([previous_path, previous_path+'.meta'])
        report = {'schema': 1, 'pack': config['pack'], 'scope': 'Texture-only source-detail restoration',
            'archive': archive_path, 'archive_sha256': config['archive_sha256'],
            'source_member': config['member'], 'source_texture_sha256': config['texture_sha256'],
            'output': output_path, 'output_sha256': digest(payload),
            'source_dimensions': config['source_dimensions'],
            'previous_dimensions': config['previous_dimensions'],
            'previous_texture': previous_path, 'previous_texture_sha256': config['previous_sha256'],
            'previous_texture_bytes': config['previous_bytes'], 'restored_texture_bytes': len(payload),
            'texture_payload_added_bytes': len(payload)-config['previous_bytes'],
            'texture_guid_preserved': config['guid'], 'existing_materials': references,
            'byte_exact_original_png': True, 'resizing_or_reencoding': False,
            'native_meshes_materials_prefabs_collision_unchanged': True,
            'protected_native_inventory_sha256': config['protected_sha256'],
            'protected_native_files': protected,
            'import': {'maximum_texture_size': config['max_texture_size'],
                       'npot_scale': 0, 'mipmaps': True, 'mip_streaming': True,
                       'anisotropy': 8, 'compression': 'High-quality platform compression'},
            'authoring_script_sha256': digest(Path(__file__).read_bytes()),
            'limitations': ['Unity texture import, material appearance and GPU residency remain unverified',
                            'Only two texture inputs are restored; native geometry remains at its prior detail level',
                            'Source/archive disk size is not an installed player-build size']}
        manifest_path = folder+'/QualityRestoration.json'
        outputs[manifest_path] = (json.dumps(report, indent=2)+'\n').encode()
        outputs[manifest_path+'.meta'] = text_meta(manifest_path)
        reports.append(report)
    return outputs, reports, retired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate without writing any files')
    args = parser.parse_args()
    outputs, reports, retired = expected_outputs()
    if not args.check:
        # Verify the restored target after atomic replacement before retiring
        # the old JPEG. This preserves the prior asset on any earlier failure.
        for path, data in outputs.items():
            target = ROOT/path
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name+'.restore-tmp')
            temporary.write_bytes(data)
            temporary.replace(target)
            assert target.read_bytes() == data
        for path in retired:
            (ROOT/path).unlink(missing_ok=True)
    for path, data in outputs.items():
        assert (ROOT/path).read_bytes() == data, 'Restoration output differs: '+path
    for path in retired:
        assert not (ROOT/path).exists(), 'Reduced duplicate remains: '+path
    # GUID uniqueness within each pack confirms the moved JPEG metadata did not
    # leave a second importer owning the same external material reference.
    for config in CONFIG:
        matches = [p for p in (ROOT/BASE/config['pack']).rglob('*.meta')
                   if re.search(r'^guid: '+config['guid']+r'$', p.read_text(), re.M)]
        assert len(matches) == 1 and matches[0].name == config['output_name']+'.meta'
        protected_native(config)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'restore',
        'restored_textures': len(reports), 'source_archives': len(reports),
        'texture_payload_added_bytes': sum(r['texture_payload_added_bytes'] for r in reports),
        'unchanged_native_files': sum(len(r['protected_native_files']) for r in reports),
        'output_files': len(outputs), 'retired_reduced_files': retired,
        'restorations': [{k: r[k] for k in ['pack', 'source_dimensions', 'previous_dimensions',
                         'restored_texture_bytes', 'texture_payload_added_bytes',
                         'texture_guid_preserved']} for r in reports],
        'unity_runtime_verified': False}, indent=2))


if __name__ == '__main__':
    main()
