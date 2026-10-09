"""Parse C# grammar; this does not compile against Unity assemblies."""
from pathlib import Path
import json
import sys
from tree_sitter import Language, Parser
import tree_sitter_c_sharp

ROOT = Path(__file__).resolve().parents[1]
parser = Parser(Language(tree_sitter_c_sharp.language()))
files = sorted((ROOT / 'Assets').rglob('*.cs'))
errors = []
for path in files:
    tree = parser.parse(path.read_bytes())
    if not tree.root_node.has_error:
        continue
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == 'ERROR' or node.is_missing:
            errors.append({'file': str(path.relative_to(ROOT)),
                           'line': node.start_point.row + 1, 'type': node.type})
        stack.extend(reversed(node.children))
report = {'status': 'FAIL' if errors else 'PASS', 'files': len(files), 'errors': errors,
          'scope': 'C# syntax grammar only; Unity API/type resolution and shader compilation are unverified'}
(ROOT / 'Validation/Revision08_SyntaxChecks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
sys.exit(bool(errors))
