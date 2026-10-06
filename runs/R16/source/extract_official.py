from pathlib import Path
from zipfile import ZipFile
base=Path('runs/R16/source')
out=base/'official_extracted'
for zname, prefix in [('all_questions.zip','original_all_questions'),('D_corrected.zip','D_corrected')]:
    target=out/prefix
    target.mkdir(parents=True,exist_ok=True)
    with ZipFile(base/zname) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            dest=(target/info.filename).resolve()
            if target.resolve() not in dest.parents:
                raise ValueError('unsafe archive path')
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(z.read(info))
            print(f'{dest.relative_to(base.resolve())}\t{info.file_size}')

