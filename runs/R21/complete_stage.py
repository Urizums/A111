"""Serial terminal integration through the unchanged queue controller."""
import runpy
import sys
from pathlib import Path
manage=Path(__file__).resolve().with_name('manage.py')
for arguments in [
    ['freeze','--scope','runs/R21/final','--lock','runs/R21/final-lock.json'],
    ['finish','--task','R21-03','--result','runs/R21/R21-03-result.json'],
]:
    sys.argv=[str(manage),*arguments]
    runpy.run_path(str(manage),run_name='__main__')
