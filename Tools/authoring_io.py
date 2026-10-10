"""Read raw, gzip, or byte-partitioned authoring inventories."""
from pathlib import Path
import gzip
import json

def read_authoring(path):
    path = Path(path)
    if path.exists():
        return json.loads(path.read_bytes().decode('utf-8'))
    compressed = Path(str(path) + '.gz')
    if compressed.exists():
        payload = compressed.read_bytes()
    else:
        parts = sorted(path.parent.glob(path.name + '.gz.part*'))
        if not parts:
            raise FileNotFoundError('Missing authoring inventory: ' + str(path))
        expected = [path.name + '.gz.part%03d' % (i + 1) for i in range(len(parts))]
        if [part.name for part in parts] != expected:
            raise ValueError('Authoring archive parts are incomplete')
        payload = b''.join(part.read_bytes() for part in parts)
    return json.loads(gzip.decompress(payload).decode('utf-8'))
