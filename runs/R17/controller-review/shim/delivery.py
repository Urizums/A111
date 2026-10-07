from pathlib import Path
def read_file(root, name): return (Path(root) / name).read_bytes()
