import os
import cv2
import numpy as np
from PIL import Image, ImageFilter

OUTPUT_DIR = r"e:\today\Today\assets\images\characters"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANVAS_W = 512
CANVAS_H = 680

def remove_white_bg(img_path, crop_box, threshold=35):
    """흰색 배경에서 인물 상반신을 자연스럽게 투명 추출"""
    img = Image.open(img_path).convert("RGBA")
    cropped = img.crop(crop_box)
    w, h = cropped.size
    
    corners = [cropped.getpixel((0,0)), cropped.getpixel((w-1,0)), cropped.getpixel((0,h-1)), cropped.getpixel((w-1,h-1))]
    bg_r = sum(c[0] for c in corners) // 4
    bg_g = sum(c[1] for c in corners) // 4
    bg_b = sum(c[2] for c in corners) // 4

    datas = cropped.getdata()
    new_data = []
    for item in datas:
        r, g, b, a = item
        diff = ((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2) ** 0.5
        if diff < threshold:
            new_data.append((r, g, b, 0))
        elif diff < threshold + 30:
            alpha = int(255 * (diff - threshold) / 30)
            new_data.append((r, g, b, alpha))
        else:
            new_data.append((r, g, b, 255))
    cropped.putdata(new_data)
    return cropped

def extract_npc_bust(img_path, rect_params=(0.10, 0.05, 0.80, 0.90)):
    """OpenCV GrabCut으로 1024x1024 초상화에서 상반신 인물만 투명 추출"""
    img = cv2.imread(img_path)
    h, w = img.shape[:2]

    rx, ry, rw, rh = rect_params
    rect = (int(w * rx), int(h * ry), int(w * rw), int(h * rh))
    
    mask = np.zeros((h, w), np.uint8)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 4, cv2.GC_INIT_WITH_RECT)
    
    fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype('uint8')
    
    # 테두리 페더링
    fg_mask = cv2.GaussianBlur(fg_mask, (11, 11), 0)
    
    b, g, r = cv2.split(img)
    bgra = cv2.merge([r, g, b, fg_mask])
    pil_img = Image.fromarray(bgra)
    
    # 바운딩 박스 크롭
    alpha = bgra[:, :, 3]
    y_idx, x_idx = np.where(alpha > 30)
    if len(y_idx) > 0:
        crop_box = (max(0, x_idx.min() - 10), max(0, y_idx.min() - 10), min(w, x_idx.max() + 10), min(h, y_idx.max() + 10))
        pil_img = pil_img.crop(crop_box)
    
    return pil_img

def compose_on_canvas(sprite_img, scale_w, scale_h, pos_y, pos_x=None):
    """
    512x680 표준 캔버스에 인물 상반신 배치
    - scale_w, scale_h: 리사이즈할 가로, 세로 크기
    - pos_y: 상단 Y 시작 위치 (키 큰 사람은 상단 20~30px, 키 작은 사람은 140~170px)
    """
    resized = sprite_img.resize((scale_w, scale_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    if pos_x is None:
        pos_x = (CANVAS_W - scale_w) // 2
    canvas.paste(resized, (pos_x, pos_y), resized)
    return canvas

# -------------------------------------------------------------
# 1. 남성 장신 (char_male_tall): 상반신이 많이 보임 (머리~어깨~가슴~허리선)
print("1. Generating char_male_tall (상반신 많이 보임, 훤칠한 높이)...")
tall_male_src = r"C:\Users\eska\.gemini\antigravity-ide\brain\637f2634-163b-4f48-8af3-687df2a76949\char_male_tall_1789977373252.jpg"
# Head starts at Y=44, Belt/Waist at Y=660. BBox X: 140~740
bust_tall_m = remove_white_bg(tall_male_src, (140, 40, 740, 680), threshold=35)
# 리사이즈: 높이 580px (상반신이 길고 풍성하게 많이 보임), 상단 20px에서 시작
img_tall_m = compose_on_canvas(bust_tall_m, scale_w=480, scale_h=580, pos_y=25)
img_tall_m.save(os.path.join(OUTPUT_DIR, "char_male_tall.png"), "PNG")

# -------------------------------------------------------------
# 2. 남성 단신 (char_male_short): 상반신이 적게 보임 (머리~어깨~윗가슴 위주, 아래쪽 배치)
print("2. Generating char_male_short (상반신 적게 보임, 낮은 높이)...")
short_male_src = r"C:\Users\eska\.gemini\antigravity-ide\brain\637f2634-163b-4f48-8af3-687df2a76949\char_male_short_1789977395777.jpg"
# Head starts at Y=98, Upper chest at Y=480. BBox X: 200~720 (상반신 윗부분만 크롭)
bust_short_m = remove_white_bg(short_male_src, (200, 90, 720, 480), threshold=35)
# 리사이즈: 높이 380px, 상단 160px에서 시작 (머리가 낮고 가슴 윗부분만 보임)
img_short_m = compose_on_canvas(bust_short_m, scale_w=420, scale_h=380, pos_y=160)
img_short_m.save(os.path.join(OUTPUT_DIR, "char_male_short.png"), "PNG")

# -------------------------------------------------------------
# 3. 남성 비만/풍채 (char_male_stout): 넓은 어깨와 둥글고 풍채 좋은 상반신
print("3. Generating char_male_stout (풍채 좋은 상인 상반신)...")
merchant_src = r"e:\today\Today\assets\images\npc_merchant.jpg"
bust_stout_m = extract_npc_bust(merchant_src, rect_params=(0.08, 0.08, 0.84, 0.88))
# 가로 폭을 넓혀 둥글고 묵직한 체형 강조 (가로 510, 세로 520, pos_y=70)
img_stout_m = compose_on_canvas(bust_stout_m, scale_w=505, scale_h=520, pos_y=75)
img_stout_m.save(os.path.join(OUTPUT_DIR, "char_male_stout.png"), "PNG")

# -------------------------------------------------------------
# 4. 남성 수척/마름 (char_male_thin): 좁은 어깨, 마른 골격의 사제/학자 상반신
print("4. Generating char_male_thin (마른 사제/학자 상반신)...")
cleric_src = r"e:\today\Today\assets\images\npc_cleric.jpg"
bust_thin_m = extract_npc_bust(cleric_src, rect_params=(0.14, 0.06, 0.72, 0.90))
# 가로 폭을 좁혀 수척한 체구 표현 (가로 380, 세로 560, pos_y=45)
img_thin_m = compose_on_canvas(bust_thin_m, scale_w=380, scale_h=560, pos_y=45)
img_thin_m.save(os.path.join(OUTPUT_DIR, "char_male_thin.png"), "PNG")

# -------------------------------------------------------------
# 5. 여성 장신 (char_female_tall): 상반신이 많이 보이는 장신 여전사
print("5. Generating char_female_tall (상반신 많이 보이는 장신 여전사)...")
mercenary_src = r"e:\today\Today\assets\images\npc_mercenary.jpg"
bust_tall_f = extract_npc_bust(mercenary_src, rect_params=(0.10, 0.05, 0.80, 0.92))
# 상단 30px에서 시작하여 가슴과 갑주, 허리선까지 넉넉하게 많이 보임 (가로 450, 세로 560)
img_tall_f = compose_on_canvas(bust_tall_f, scale_w=450, scale_h=560, pos_y=30)
img_tall_f.save(os.path.join(OUTPUT_DIR, "char_female_tall.png"), "PNG")

# -------------------------------------------------------------
# 6. 여성 단신 (char_female_short): 상반신이 적게 보이는 아담한 여성
print("6. Generating char_female_short (상반신 적게 보이는 단신 여성)...")
peasant_src = r"e:\today\Today\assets\images\npc_peasant.jpg"
# 머리부터 윗가슴 위주로만 크롭
bust_short_f = extract_npc_bust(peasant_src, rect_params=(0.15, 0.10, 0.70, 0.72))
# 상단 150px에서 시작하여 아담하게 윗부분만 보임 (가로 390, 세로 390)
img_short_f = compose_on_canvas(bust_short_f, scale_w=390, scale_h=390, pos_y=150)
img_short_f.save(os.path.join(OUTPUT_DIR, "char_female_short.png"), "PNG")

# -------------------------------------------------------------
# 7. 여성 비만/풍채 (char_female_stout): 넉넉하고 둥근 체구의 여성
print("7. Generating char_female_stout (풍채 있는 여성 상반신)...")
bust_stout_f = extract_npc_bust(peasant_src, rect_params=(0.08, 0.08, 0.84, 0.88))
# 가로 폭 1.25배 팽창 (가로 490, 세로 500, pos_y=80)
img_stout_f = compose_on_canvas(bust_stout_f, scale_w=490, scale_h=500, pos_y=80)
img_stout_f.save(os.path.join(OUTPUT_DIR, "char_female_stout.png"), "PNG")

# -------------------------------------------------------------
# 8. 여성 수척/마름 (char_female_thin): 호리호리하고 마른 체형의 여성
print("8. Generating char_female_thin (수척한 여성 상반신)...")
suspicious_src = r"e:\today\Today\assets\images\npc_suspicious.jpg"
bust_thin_f = extract_npc_bust(suspicious_src, rect_params=(0.14, 0.08, 0.72, 0.88))
# 가로 폭 0.82배 축소 (가로 375, 세로 540, pos_y=45)
img_thin_f = compose_on_canvas(bust_thin_f, scale_w=375, scale_h=540, pos_y=45)
img_thin_f.save(os.path.join(OUTPUT_DIR, "char_female_thin.png"), "PNG")

print("\n[SUCCESS] All 8 upper-body character sprites generated successfully!")
