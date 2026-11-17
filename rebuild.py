"""Rebuild all documents and the standalone selector after editing master.json."""
from pathlib import Path
import os,subprocess,sys,shutil
root=Path(__file__).resolve().parent
node=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node')
if not node:raise SystemExit('Node.js is required to rebuild PDF and Word editions.')
for command in [[sys.executable,str(root/'prepare.py')],[node,str(root/'build_editions.cjs'),*sys.argv[1:]],[sys.executable,str(root/'make_selector.py')]]:
 subprocess.run(command,cwd=root,check=True)
