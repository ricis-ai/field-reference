"""Optional tagged PDF export from current DOCX files. Requires LibreOffice."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--soffice',default=shutil.which('soffice'),help='Path to LibreOffice soffice executable')
a=p.parse_args()
if not a.soffice:raise SystemExit('Install LibreOffice or pass --soffice /path/to/soffice')
root=Path(__file__).resolve().parent;dest=root/'tagged';dest.mkdir(exist_ok=True)
inputs=[root/'AB9MZ_Amateur_Radio_Field_Reference.docx',*sorted((root/'sections').glob('*.docx'))]
with tempfile.TemporaryDirectory(prefix='ab9mz_tagged_') as profile:
 subprocess.run([a.soffice,'-env:UserInstallation='+Path(profile).as_uri(),'--headless','--convert-to','pdf:writer_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"true"},"ExportBookmarks":{"type":"boolean","value":"true"}}','--outdir',str(dest),*[str(f) for f in inputs]],check=True)
missing=[f.stem for f in inputs if not (dest/(f.stem+'.pdf')).is_file()]
if missing:raise SystemExit('Missing exports: '+', '.join(missing))
print('Tagged review exports created. Inspect reading order and screen-reader behavior before release.')
