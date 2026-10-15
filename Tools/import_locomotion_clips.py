"""Fetch two MIT Rocketbox transitions from pinned, checksum-verified sources."""
from pathlib import Path
from urllib.request import Request, urlopen
import argparse
import hashlib
import json
import uuid

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '0943055db6ec570bcef9f2c8b41c9e5467c808f9'
DIRECTORY = 'Assets/Game/Foundation/Animations/Rocketbox'
LICENSE_FILE = 'Documentation/Licenses/Microsoft_Rocketbox_MIT.md'
LICENSE_SHA256 = '17474e386e0b9e1a700cc3d06b2b0882a2c376d9c6b49c7f8274409b8f8d2352'
SOURCES = {
    'RunStart': ('m_run_start.max.fbx',
                 'aba4486443fc3845f6d9b3d5b11d0fec9cfaeb39687b0e32d5b69493a130979d',
                 'cac897d67eb3375fc590e788e32bf31d5cedede6'),
    'RunStop': ('m_run_stop.max.fbx',
                '1eb03637281bd5c363ef2262321ca3322fc55387f33c09213528a67b6058202c',
                'f0aa0ee5b787e4d9f6503a9dadce10d627dbf9b1'),
}


def import_clips(cache=None):
    if hashlib.sha256((ROOT / LICENSE_FILE).read_bytes()).hexdigest() != LICENSE_SHA256:
        raise ValueError('The original Rocketbox MIT copyright/license must be retained.')
    records = []
    for name, (filename, expected, blob) in SOURCES.items():
        relative = f'{DIRECTORY}/{name}.fbx'
        destination = ROOT / relative
        upstream = f'Assets/Animations/all_animations_max_motextr_xy/{filename}'
        url = f'https://raw.githubusercontent.com/microsoft/Microsoft-Rocketbox/{COMMIT}/{upstream}'
        candidate = cache / filename if cache else destination
        if candidate.is_file():
            data = candidate.read_bytes()
        else:
            request = Request(url, headers={'User-Agent': 'ALCATRAZ-locomotion-import'})
            with urlopen(request, timeout=45) as response:
                data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Source checksum mismatch: {name}')
        computed = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if computed != blob or not data.startswith(b'Kaydara FBX Binary'):
            raise ValueError(f'Source identity/format mismatch: {name}')
        if destination.is_file() and destination.read_bytes() != data:
            raise ValueError(f'Refusing to replace modified source: {relative}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        metadata = Path(str(destination) + '.meta')
        if not metadata.exists():
            guid = uuid.uuid5(uuid.NAMESPACE_URL, relative).hex
            metadata.write_text(f'fileFormatVersion: 2\nguid: {guid}\nModelImporter:\n'
                                '  externalObjects: {}\n  userData: \n'
                                '  assetBundleName: \n  assetBundleVariant: \n')
        records.append({'path': relative, 'source': upstream, 'source_url': url,
                        'sha256': expected, 'git_blob_sha1': blob, 'bytes': len(data),
                        'upstream_html_blob_prefix': blob[:7],
                        'upstream_html_url': f'https://github.com/microsoft/Microsoft-Rocketbox/blob/{COMMIT}/{upstream}'})
    provenance = {'repository': 'https://github.com/microsoft/Microsoft-Rocketbox',
                  'repository_commit': COMMIT, 'license': 'MIT',
                  'license_file': LICENSE_FILE,
                  'license_sha256': LICENSE_SHA256,
                  'files': records,
                  'identity_scope': 'Downloaded from pinned HTTPS URLs. SHA256 and computed Git blob hashes are retained. GitHub source HTML independently exposed matching seven-character blob prefixes, not full upstream blob IDs.',
                  'usage': 'Original Microsoft Rocketbox running start/stop clips; no Rockstar assets.'}
    (ROOT / 'Documentation/LocomotionClipProvenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'Verified/imported {len(records)} licensed locomotion transitions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, help='Optional existing download folder; checksums are still required.')
    import_clips(parser.parse_args().cache_dir)
