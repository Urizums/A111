from pathlib import Path
import zipfile
for name in ('D_corrected.zip','all_questions.zip'):
    print(f'[{name}]')
    with zipfile.ZipFile(Path('runs/R16/source')/name) as z:
        for info in z.infolist():
            print(f'{info.filename} | {info.file_size} bytes')
