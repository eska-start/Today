import os
from PIL import Image, ImageOps, ImageFilter

OUTPUT_DIR = r"e:\today\Today\assets\images\characters"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def remove_white_background(img_path, threshold=40):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    corners = [img.getpixel((0, 0)), img.getpixel((w-1, 0)), img.getpixel((0, h-1)), img.getpixel((w-1, h-1))]
    tr = sum(c[0] for c in corners) // 4
    tg = sum(c[1] for c in corners) // 4
    tb = sum(c[2] for c in corners) // 4

    datas = img.getdata()
    new_data = []
    for item in datas:
        r, g, b, a = item
        diff = ((r - tr)**2 + (g - tg)**2 + (b - tb)**2) ** 0.5
        if diff < threshold:
            new_data.append((r, g, b, 0))
        elif diff < threshold + 25:
            alpha = int(255 * (diff - threshold) / 25)
            new_data.append((r, g, b, alpha))
        else:
            new_data.append((r, g, b, 255))
    img.putdata(new_data)
    return img

def cutout_portrait(img_path, scale_x=1.0, scale_y=1.0, is_female=False):
    """
    일러스트 이미지에서 인물 중심부를 타원/버스트 마스크로 깔끔하게 컷아웃하여
    체형 비율(scale_x, scale_y)을 조절한 투명 PNG 생성
    """
    base = Image.open(img_path).convert("RGBA")
    w, h = base.size

    # 인물 중심 타원형 투명 마스크 생성 (배경 자연스럽게 페더링 투명화)
    mask = Image.new("L", (w, h), 0)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    
    # 상반신/전신 영역 타원 그리기 (외곽 부드럽게 감쇄)
    cx, cy = w // 2, int(h * 0.48)
    rx, ry = int(w * 0.44), int(h * 0.48)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    
    # 블러로 부드러운 외곽선 페더링
    mask = mask.filter(ImageFilter.GaussianBlur(14))
    base.putalpha(mask)

    # 체형 비율 조정 (뚱뚱함은 가로로 넓게, 마름은 가로로 좁게, 키 큰 사람은 세로로 길게)
    target_w = int(w * scale_x)
    target_h = int(h * scale_y)
    resized = base.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # 512x680 표준 캔버스 중앙 배치
    canvas = Image.new("RGBA", (512, 680), (0, 0, 0, 0))
    pos_x = (512 - target_w) // 2
    pos_y = (680 - target_h) // 2
    
    # Y 위치 보정 (키가 작은 사람은 아래쪽에, 큰 사람은 꽉 차게)
    if scale_y < 0.95:
        pos_y += 50
    elif scale_y > 1.05:
        pos_y -= 25

    canvas.paste(resized, (pos_x, pos_y), resized)
    return canvas

# 1. AI 생성 순수 흰색 배경 캐릭터 2종 투명화
tall_male_src = r"C:\Users\eska\.gemini\antigravity-ide\brain\637f2634-163b-4f48-8af3-687df2a76949\char_male_tall_1789977373252.jpg"
short_male_src = r"C:\Users\eska\.gemini\antigravity-ide\brain\637f2634-163b-4f48-8af3-687df2a76949\char_male_short_1789977395777.jpg"

print("1. Converting tall male...")
img_tall = remove_white_background(tall_male_src, threshold=35)
img_tall = img_tall.resize((512, 680), Image.Resampling.LANCZOS)
img_tall.save(os.path.join(OUTPUT_DIR, "char_male_tall.png"), "PNG")

print("2. Converting short male...")
img_short = remove_white_background(short_male_src, threshold=35)
# 키 작은 사람은 캔버스 내에서 높이를 낮추고 아래쪽에 위치
img_short_scaled = img_short.resize((410, 540), Image.Resampling.LANCZOS)
canvas_short = Image.new("RGBA", (512, 680), (0, 0, 0, 0))
canvas_short.paste(img_short_scaled, ((512 - 410) // 2, 680 - 540 - 15), img_short_scaled)
canvas_short.save(os.path.join(OUTPUT_DIR, "char_male_short.png"), "PNG")

# 3. 뚱뚱한 남성 (char_male_stout): 상인 베이스, 폭 1.3배 팽창, 둥근 체구
print("3. Generating stout male...")
merchant_src = r"e:\today\Today\assets\images\npc_merchant.jpg"
img_stout_m = cutout_portrait(merchant_src, scale_x=1.32, scale_y=0.98)
img_stout_m.save(os.path.join(OUTPUT_DIR, "char_male_stout.png"), "PNG")

# 4. 마른 남성 (char_male_thin): 사제/학자 베이스, 폭 0.82배 수척, 장신
print("4. Generating thin male...")
cleric_src = r"e:\today\Today\assets\images\npc_cleric.jpg"
img_thin_m = cutout_portrait(cleric_src, scale_x=0.82, scale_y=1.08)
img_thin_m.save(os.path.join(OUTPUT_DIR, "char_male_thin.png"), "PNG")

# 5. 키 큰 여성 (char_female_tall): 용병/전사 베이스 컷아웃, 장신 1.12배
print("5. Generating tall female...")
mercenary_src = r"e:\today\Today\assets\images\npc_mercenary.jpg"
img_tall_f = cutout_portrait(mercenary_src, scale_x=0.95, scale_y=1.12, is_female=True)
img_tall_f.save(os.path.join(OUTPUT_DIR, "char_female_tall.png"), "PNG")

# 6. 키 작은 여성 (char_female_short): 농민/평민 베이스, 단신 0.82배
print("6. Generating short female...")
peasant_src = r"e:\today\Today\assets\images\npc_peasant.jpg"
img_short_f = cutout_portrait(peasant_src, scale_x=0.88, scale_y=0.84, is_female=True)
img_short_f.save(os.path.join(OUTPUT_DIR, "char_female_short.png"), "PNG")

# 7. 뚱뚱한 여성 (char_female_stout): 폭 1.28배, 넉넉하고 푸근한 체형
print("7. Generating stout female...")
img_stout_f = cutout_portrait(peasant_src, scale_x=1.28, scale_y=0.95, is_female=True)
img_stout_f.save(os.path.join(OUTPUT_DIR, "char_female_stout.png"), "PNG")

# 8. 마른 여성 (char_female_thin): 가냘픈 0.78배 폭, 수척한 체형
print("8. Generating thin female...")
suspicious_src = r"e:\today\Today\assets\images\npc_suspicious.jpg"
img_thin_f = cutout_portrait(suspicious_src, scale_x=0.80, scale_y=1.02, is_female=True)
img_thin_f.save(os.path.join(OUTPUT_DIR, "char_female_thin.png"), "PNG")

print("All 8 transparent character sprites created successfully in", OUTPUT_DIR)
