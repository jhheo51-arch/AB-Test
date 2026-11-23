"""Portable tutorial paths; never write generated media into the source app."""
import argparse, os, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--app-dir', type=Path, default=ROOT.parent/'app')
parser.add_argument('--output-dir', type=Path, default=Path(os.environ.get('TMPDIR', tempfile.gettempdir()))/'ab_walkthrough_reproduction')
parser.add_argument('--quick', action='store_true')
args = parser.parse_args()
RUNTIME = args.app_dir.resolve()
WORK = args.output_dir.resolve()
if WORK == ROOT or ROOT in WORK.parents or WORK == RUNTIME or RUNTIME in WORK.parents:
    parser.error('Output must be outside tutorial/ and the source app')
WORK.mkdir(parents=True, exist_ok=True)
for key in ('TMPDIR', 'TEMP', 'TMP'):
    os.environ[key] = str(WORK)
HELP = WORK/'help'
HELP.mkdir(exist_ok=True)
