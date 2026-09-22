import os
import shutil
from PIL import Image
import numpy as np

BRAIN_DIR = r"C:\Users\eska\.gemini\antigravity-ide\brain\637f2634-163b-4f48-8af3-687df2a76949"
TARGET_DIR = r"e:\today\Today\assets\images\characters"
os.makedirs(TARGET_DIR, exist_ok=True)

AI_MAPPING = {
    "char_male_tall.jpg": "char_male_tall_1790035119175.jpg",
    "char_male_short.jpg": "char_male_short_1790035131458.jpg",
    "char_male_stout.jpg": "char_male_stout_1790035146696.jpg",
    "char_male_thin.jpg": "char_male_thin_1790035159025.jpg",
    "char_female_tall.jpg": "char_female_tall_1790035171783.jpg",
    "char_female_short.jpg": "char_female_short_1790035185787.jpg",
    "char_female_stout.jpg": "char_female_stout_1790035197945.jpg",
    "char_female_thin.jpg": "char_female_thin_1790035211067.jpg",
    "char_noble_bribe.jpg": "char_noble_bribe_1790035223770.jpg",
    "char_orc_tourist.jpg": "char_orc_tourist_1790035238861.jpg",
    "char_monster_disguise.jpg": "char_monster_disguise_1790035253977.jpg",
}

def clean_magenta_background(img_path, out_jpg_path, out_png_path):
    """
    마젠타(R:255, G:0, B:255) 부근의 배경을 완벽한 순수 마젠타 (255, 0, 255)로 고정하고,
    동시에 투명 PNG도 함께 생성
    """
    im = Image.open(img_path).convert("RGBA")
    arr = np.array(im, dtype=np.float32)
    
    # 마젠타 색상 거리 계산: dist to (255, 0, 255)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    
    # Chroma key distance
    dist = np.sqrt((r - 255)**2 + (g - 0)**2 + (b - 255)**2)
    
    # 마젠타 배경 마스크
    bg_mask = dist < 70
    
    # 순수 마젠타 배경 JPG 생성
    arr_jpg = np.array(im.convert("RGB"))
    arr_jpg[bg_mask] = [255, 0, 255]
    Image.fromarray(arr_jpg).save(out_jpg_path, "JPEG", quality=98)
    
    # 투명 PNG 생성 (부드러운 안티앨리어싱)
    alpha = np.ones_like(dist) * 255
    # 완전 배경
    alpha[dist < 45] = 0
    # 경계선 페더링
    feather = (dist >= 45) & (dist < 70)
    alpha[feather] = (dist[feather] - 45) / (70 - 45) * 255
    
    arr_png = np.array(im)
    arr_png[:, :, 3] = alpha.astype(np.uint8)
    Image.fromarray(arr_png).save(out_png_path, "PNG")

def make_magenta_for_existing(img_path, out_jpg_path, out_png_path):
    """기존 흰색/밝은 배경 이미지를 순수 마젠타 배경 및 투명 PNG로 변환"""
    im = Image.open(img_path).convert("RGBA")
    arr = np.array(im)
    r = arr[:, :, 0].astype(float)
    g = arr[:, :, 1].astype(float)
    b = arr[:, :, 2].astype(float)
    
    # 코너 기준 배경색
    bg_r = (r[0,0] + r[0,-1] + r[-1,0] + r[-1,-1]) / 4
    bg_g = (g[0,0] + g[0,-1] + g[-1,0] + g[-1,-1]) / 4
    bg_b = (b[0,0] + b[0,-1] + b[-1,0] + b[-1,-1]) / 4
    
    diff = np.sqrt((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2)
    bg_mask = diff < 40
    
    # 순수 마젠타 JPG
    arr_jpg = np.array(im.convert("RGB"))
    arr_jpg[bg_mask] = [255, 0, 255]
    Image.fromarray(arr_jpg).save(out_jpg_path, "JPEG", quality=98)
    
    # 투명 PNG
    alpha = np.ones_like(diff) * 255
    alpha[diff < 30] = 0
    feather = (diff >= 30) & (diff < 50)
    alpha[feather] = (diff[feather] - 30) / (50 - 30) * 255
    arr_png = np.array(im)
    arr_png[:, :, 3] = alpha.astype(np.uint8)
    Image.fromarray(arr_png).save(out_png_path, "PNG")

print("1. Processing AI generated magenta images...")
for target_name, src_name in AI_MAPPING.items():
    src_path = os.path.join(BRAIN_DIR, src_name)
    base_name = os.path.splitext(target_name)[0]
    out_jpg = os.path.join(TARGET_DIR, target_name)
    out_png = os.path.join(TARGET_DIR, base_name + ".png")
    clean_magenta_background(src_path, out_jpg, out_png)
    print(f"  Processed {target_name} -> JPG & PNG")

print("\n2. Processing remaining special characters...")
remaining = ["char_ghost_visitor.jpg", "char_plague_visitor.jpg", "char_mage_unregistered.jpg"]
for rem in remaining:
    src_path = os.path.join(TARGET_DIR, rem)
    base_name = os.path.splitext(rem)[0]
    out_png = os.path.join(TARGET_DIR, base_name + ".png")
    make_magenta_for_existing(src_path, src_path, out_png)
    print(f"  Processed {rem} -> pure magenta background & PNG")

print("\n[COMPLETE] All 14 characters now have pure RGB(255, 0, 255) background and transparent PNGs!")
