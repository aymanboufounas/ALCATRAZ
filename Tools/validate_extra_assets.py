"""Check the native extras catalog and optional supplied ZIP hashes without importing."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import sys
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Assets/Game/Supplied/Resources/AlcatrazExtras'
OFFICIAL_SHADERS = {'933532a4fcc9baf4fa0491de14d08ed7'}
CATALOG = ast.literal_eval(next(
    node.value for node in ast.parse((ROOT / 'Tools/import_revision12.py').read_text()).body
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CATALOG' for t in node.targets)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    errors, results = [], []
    catalog = json.loads((BASE / 'Catalog.json').read_text())
    entries = {e['name']: e for e in catalog}
    if len(entries) != len(catalog) or set(entries) != {n for n, _ in CATALOG}:
        errors.append('Catalog names must be unique and match the import catalog')
    guids = {}
    for meta in (ROOT / 'Assets').rglob('*.meta'):
        match = re.search(r'^guid: ([a-f0-9]{32})$', meta.read_text(), re.M)
        if match:
            guids[match[1]] = Path(str(meta)[:-5])
    world = (ROOT / 'Assets/Game/Supplied/Scripts/SuppliedExtrasWorld.cs').read_text()
    equipment = (ROOT / 'Assets/Game/Foundation/Scripts/WeaponState.cs').read_text()
    for name, archive in CATALOG:
        entry = entries.get(name)
        if entry is None:
            errors.append('Missing catalog entry: ' + name)
            continue
        folder = BASE / name
        prefab = folder / (name + '.prefab')
        if json.loads((folder / 'Source.json').read_text()) != entry:
            errors.append(name + ': catalog differs from source provenance')
        if entry['resource'] != 'AlcatrazExtras/' + name + '/' + name:
            errors.append(name + ': resource path differs from native prefab')
        if not prefab.is_file() or not Path(str(prefab) + '.meta').is_file():
            errors.append(name + ': native prefab or metadata missing')
        if 'Model("' + name + '"' not in world and not re.search(r'\b' + name + r'\b', equipment):
            errors.append(name + ': no annex placement or equipment slot')
        counts = {'meshes': 0, 'materials': 0, 'textures': 0}
        for asset in folder.rglob('*'):
            if not asset.is_file() or asset.suffix == '.meta' or asset.name == 'Source.json':
                continue
            if not Path(str(asset) + '.meta').is_file():
                errors.append(name + ': metadata missing for ' + asset.name)
            if asset.suffix in ('.prefab', '.mat', '.asset'):
                for guid in re.findall(r'guid: ([a-f0-9]{32})', asset.read_text()):
                    if guid == '0' * 32 or guid in OFFICIAL_SHADERS:
                        continue
                    if guid not in guids or not guids[guid].exists():
                        errors.append(name + ': unresolved reference ' + guid + ' in ' + asset.name)
            if asset.suffix == '.asset':
                counts['meshes'] += 1
            elif asset.suffix == '.mat':
                counts['materials'] += 1
            elif asset.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                counts['textures'] += 1
                with Image.open(asset) as image:
                    image.verify()
        if not counts['meshes'] or not counts['materials']:
            errors.append(name + ': missing native meshes or materials')
        if counts['textures'] != entry['textures']:
            errors.append(name + ': texture count differs from provenance')
        archive_status = 'not supplied'
        if args.archives:
            path = args.archives / archive
            # The latest barrel upload omits the earlier duplicate-name suffix.
            if name == 'ExplosiveBarrel' and not path.exists():
                path = args.archives / 'explosive-barrel.zip'
            if path.is_file():
                archive_status = 'matched' if hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'] else 'mismatch'
                if archive_status == 'mismatch':
                    errors.append(name + ': supplied archive hash differs')
                with zipfile.ZipFile(path) as z:
                    bad = z.testzip()
                    if bad:
                        errors.append(name + ': ZIP checksum failed for ' + bad)
        results.append({'name': name, 'archive': archive, 'resource': entry['resource'],
                        'source_sha256': entry['sha256'], 'archive_status': archive_status,
                        **counts})
    report = {'status': 'FAIL' if errors else 'PASS', 'packs': len(results),
              'matched_archives': sum(r['archive_status'] == 'matched' for r in results),
              'errors': errors, 'assets': results,
              'scope': 'Native prefab/material/texture references, catalog provenance, placement/equipment registration and supplied ZIP hashes/CRC. Unity import and gameplay are unverified.'}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'assets'}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
