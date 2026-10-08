from pathlib import Path
import json
from PIL import Image,ImageChops
V2=Path(__file__).resolve().parents[1]
def main():
    rows=[]
    for name in ['paper','technical_report']:
        for p in sorted((V2/'qa/pdf'/name).glob('page-*.png')):
            old=V2/'qa/reader-feedback-before-final-wording'/name/p.name
            a=Image.open(p).convert('RGB');b=Image.open(old).convert('RGB');assert a.size==b.size
            bbox=ImageChops.difference(a,b).getbbox()
            rows.append({'document':name,'page':int(p.stem[-2:]),'pixel_identical_to_full_page_already_viewed':bbox is None,'changed_pixel_box':bbox,'final_image':str(p)})
    (V2/'qa/final_page_comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([r for r in rows if not r['pixel_identical_to_full_page_already_viewed']]))
if __name__=='__main__':main()
