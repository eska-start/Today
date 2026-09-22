import os
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, gaussian_filter
from collections import deque

CHAR_DIR = r"e:\today\Today\assets\images\characters"

CHARACTERS = [
    "char_male_tall",
    "char_male_short",
    "char_male_stout",
    "char_male_thin",
    "char_female_tall",
    "char_female_short",
    "char_female_stout",
    "char_female_thin",
    "char_noble_bribe",
    "char_orc_tourist",
    "char_monster_disguise",
    "char_ghost_visitor",
    "char_plague_visitor",
    "char_mage_unregistered"
]

def clean_character_fringe(base_name):
    jpg_path = os.path.join(CHAR_DIR, f"{base_name}.jpg")
    png_path = os.path.join(CHAR_DIR, f"{base_name}.png")
    
    if not os.path.exists(jpg_path):
        print(f"[WARN] File not found: {jpg_path}")
        return
        
    im = Image.open(jpg_path).convert("RGB")
    arr = np.array(im, dtype=float)
    h, w, _ = arr.shape
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    
    # 1. 마젠타 배경 판별
    dist = np.sqrt((r - 255.0)**2 + (g - 0.0)**2 + (b - 254.0)**2)
    excess = np.maximum(0.0, np.minimum(r, b) - g)
    
    # 순수 마젠타 스크린 판정 (외곽이든 내부 고립 영역이든 모두 포함)
    is_pure_magenta = (dist < 90) | ((excess > 65) & (g < 65))
    
    # 2. 외곽 플러드필 (외곽 배경의 경계선 그라데이션까지 포착)
    is_bg_candidate = (dist < 125) | ((excess > 50) & (g < 80))
    bg_mask = np.zeros((h, w), dtype=bool)
    q = deque()
    
    for x in range(w):
        if is_bg_candidate[0, x]:
            bg_mask[0, x] = True
            q.append((0, x))
        if is_bg_candidate[h-1, x]:
            bg_mask[h-1, x] = True
            q.append((h-1, x))
    for y in range(h):
        if is_bg_candidate[y, 0]:
            bg_mask[y, 0] = True
            q.append((y, 0))
        if is_bg_candidate[y, w-1]:
            bg_mask[y, w-1] = True
            q.append((y, w-1))
            
    while q:
        cy, cx = q.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w:
                if not bg_mask[ny, nx] and is_bg_candidate[ny, nx]:
                    bg_mask[ny, nx] = True
                    q.append((ny, nx))
                    
    # 외곽 플러드필 배경 + 내부 고립 마젠타 영역 통합 (가방 끈 사이, 팔 사이 구멍 완벽 제거)
    final_bg = bg_mask | is_pure_magenta
    
    # 3. 배경 영역 1픽셀 확장 (캐릭터 외곽에 번진 핑크색 아티팩트 픽셀 제거)
    struct = np.ones((3, 3), dtype=bool)
    dilated_bg = binary_dilation(final_bg, structure=struct, iterations=1)
    
    # 4. 알파 채널 안티앨리어싱
    char_mask = (~dilated_bg).astype(float)
    alpha_smooth = gaussian_filter(char_mask, sigma=0.7)
    alpha = np.clip((alpha_smooth - 0.20) / 0.60, 0.0, 1.0) * 255.0
    
    # 5. 디스필 (Despill): 캐릭터 경계선과 전신에 걸쳐 잔류 마젠타 스필 완전 소거
    # 팽창된 경계선 영역 (외곽 4픽셀 범위)
    edge_region = binary_dilation(dilated_bg, structure=struct, iterations=4) & (alpha > 0)
    
    r_out = r.copy()
    g_out = g.copy()
    b_out = b.copy()
    
    spill = np.maximum(0.0, np.minimum(r_out, b_out) - g_out)
    
    # (A) 경계선 영역 강력 디스필
    factor = np.where(alpha < 240, 1.0, 0.85)
    r_out[edge_region] -= (spill[edge_region] * factor[edge_region])
    b_out[edge_region] -= (spill[edge_region] * factor[edge_region])
    g_out[edge_region] += (spill[edge_region] * 0.08)
    
    # (B) 내부 잔류 스필 (예: 갇힌 구멍 경계선 부근 스필)
    internal_spill = (alpha >= 240) & (spill > 30) & (g_out < 90)
    r_out[internal_spill] -= (spill[internal_spill] * 0.8)
    b_out[internal_spill] -= (spill[internal_spill] * 0.8)
    
    r_out = np.clip(r_out, 0, 255)
    g_out = np.clip(g_out, 0, 255)
    b_out = np.clip(b_out, 0, 255)
    
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 0] = np.uint8(r_out)
    rgba[:, :, 1] = np.uint8(g_out)
    rgba[:, :, 2] = np.uint8(b_out)
    rgba[:, :, 3] = np.uint8(alpha)
    
    out_img = Image.fromarray(rgba, "RGBA")
    out_img.save(png_path, "PNG", optimize=True)
    
    # 검증 통계
    edge_px = (alpha > 0) & (alpha < 255)
    rem_spill = np.maximum(0.0, np.minimum(r_out[edge_px], b_out[edge_px]) - g_out[edge_px]) if np.sum(edge_px) > 0 else []
    high_spill_count = np.sum(rem_spill > 20) if len(rem_spill) > 0 else 0
    internal_high = np.sum((alpha > 0) & (np.maximum(0.0, np.minimum(r_out, b_out) - g_out) > 35) & (g_out < 80))
    
    print(f"[{base_name}] Done. Edge Spill(>20): {high_spill_count}, Internal Hole Spill(>35): {internal_high}")

def main():
    print("=== Enhanced Chromakey Fringe Cleaning & Hole Removal ===")
    for char_id in CHARACTERS:
        clean_character_fringe(char_id)
    print("=== Complete! ===")

if __name__ == "__main__":
    main()
