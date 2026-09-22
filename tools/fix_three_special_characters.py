import os
import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes, gaussian_filter
from collections import deque

CHAR_DIR = r"e:\today\Today\assets\images\characters"

def process_plague_visitor():
    """
    char_plague_visitor: 체커보드 배경 분리
    몸통(얼굴, 손수건, 옷)에 구멍 0개 보장
    """
    jpg_path = os.path.join(CHAR_DIR, "char_plague_visitor.jpg")
    out_png = os.path.join(CHAR_DIR, "char_plague_visitor.png")
    im = Image.open(jpg_path).convert("RGB")
    arr = np.array(im, dtype=float)
    h, w, _ = arr.shape
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    # 체커보드 판별 (무채색 & 고명도)
    diff = np.maximum(np.abs(r - g), np.abs(g - b))
    is_checker = (r > 185) & (g > 185) & (b > 185) & (diff < 12)

    # 외곽 테두리에서 시작하는 Floodfill (외부 배경)
    bg_mask = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        if is_checker[0, x]: bg_mask[0, x] = True; q.append((0, x))
        if is_checker[h-1, x]: bg_mask[h-1, x] = True; q.append((h-1, x))
    for y in range(h):
        if is_checker[y, 0]: bg_mask[y, 0] = True; q.append((y, 0))
        if is_checker[y, w-1]: bg_mask[y, w-1] = True; q.append((y, w-1))

    while q:
        cy, cx = q.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w:
                if not bg_mask[ny, nx] and is_checker[ny, nx]:
                    bg_mask[ny, nx] = True
                    q.append((ny, nx))

    # 지팡이와 몸통 사이 틈새의 체커보드도 투명화
    # x: 570~670, y: 550~1000 구간의 체커보드
    staff_gap = is_checker & (np.arange(w)[None, :] > 580) & (np.arange(w)[None, :] < 670) & (np.arange(h)[:, None] > 540) & (np.arange(h)[:, None] < 1000)
    bg_mask = bg_mask | staff_gap

    fg_mask = ~bg_mask

    # 손수건, 얼굴, 피부 내부 구멍 100% 채우기
    fg_filled = binary_fill_holes(fg_mask)

    # 안티앨리어싱
    alpha = gaussian_filter(fg_filled.astype(float), sigma=0.6)
    alpha = np.clip((alpha - 0.2) / 0.6, 0.0, 1.0) * 255.0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:,:,:3] = np.uint8(arr)
    out[:,:,3] = np.uint8(alpha)

    Image.fromarray(out).save(out_png, "PNG", optimize=True)
    print("char_plague_visitor.png processed successfully with ZERO holes!")

def process_ghost_visitor():
    """
    char_ghost_visitor: 수채화 종이 배경 분리
    유령 영체(얼굴, 서류, 옷)에 구멍 0개 보장
    """
    jpg_path = os.path.join(CHAR_DIR, "char_ghost_visitor.jpg")
    out_png = os.path.join(CHAR_DIR, "char_ghost_visitor.png")
    im = Image.open(jpg_path).convert("RGB")
    arr = np.array(im, dtype=float)
    h, w, _ = arr.shape
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    # 순수 배경 종이: r > 242, g > 242, b > 238 이고 색상 편차가 매우 적으며 푸른 오라가 아님
    is_pure_paper = (r > 242) & (g > 242) & (b > 238) & (np.abs(r - g) < 7) & (np.abs(g - b) < 7) & (b <= r + 4)

    bg_mask = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        if is_pure_paper[0, x]: bg_mask[0, x] = True; q.append((0, x))
        if is_pure_paper[h-1, x]: bg_mask[h-1, x] = True; q.append((h-1, x))
    for y in range(h):
        if is_pure_paper[y, 0]: bg_mask[y, 0] = True; q.append((y, 0))
        if is_pure_paper[y, w-1]: bg_mask[y, w-1] = True; q.append((y, w-1))

    while q:
        cy, cx = q.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w:
                if not bg_mask[ny, nx] and is_pure_paper[ny, nx]:
                    bg_mask[ny, nx] = True
                    q.append((ny, nx))

    fg_mask = ~bg_mask
    fg_filled = binary_fill_holes(fg_mask)

    alpha = gaussian_filter(fg_filled.astype(float), sigma=0.8)
    alpha = np.clip((alpha - 0.15) / 0.65, 0.0, 1.0) * 255.0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:,:,:3] = np.uint8(arr)
    out[:,:,3] = np.uint8(alpha)

    Image.fromarray(out).save(out_png, "PNG", optimize=True)
    print("char_ghost_visitor.png processed successfully with ZERO holes!")

def process_mage_unregistered():
    """
    char_mage_unregistered: 정밀 GrabCut + 바디 프로텍션
    마법사 몸통/지팡이/마법책 구멍 0개 보장 & 외부 인물/배경 제거
    """
    jpg_path = os.path.join(CHAR_DIR, "char_mage_unregistered.jpg")
    out_png = os.path.join(CHAR_DIR, "char_mage_unregistered.png")
    im = cv2.imread(jpg_path)
    h, w, _ = im.shape

    mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)

    # 1. 확실한 배경 마킹
    mask[:90, :] = cv2.GC_BGD
    mask[:340, :160] = cv2.GC_BGD
    mask[:340, 580:] = cv2.GC_BGD
    mask[350:480, :260] = cv2.GC_BGD # 좌측 금발 인물 얼굴 완벽 제거
    mask[450:800, 680:] = cv2.GC_BGD # 우측 대기 줄
    mask[1050:, :] = cv2.GC_BGD      # 최하단 바닥
    mask[380:440, 365:420] = cv2.GC_BGD # 지팡이와 몸통 사이 성벽 틈새

    # 2. 전경 추정 영역 (마법사 본체 BBox)
    mask[90:1050, 160:680] = cv2.GC_PR_FGD

    # 3. 확실한 전경 (Sure Foreground - 구멍 절대 금지)
    mask[180:310, 400:520] = cv2.GC_FGD # 얼굴, 안경, 머리카락
    mask[350:750, 320:550] = cv2.GC_FGD # 로브 상체, 가슴, 책, 가방
    mask[120:300, 180:350] = cv2.GC_FGD # 지팡이 결정 및 상단
    mask[750:980, 290:570] = cv2.GC_FGD # 로브 하단

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    cv2.grabCut(im, mask, None, bgdModel, fgdModel, 6, cv2.GC_INIT_WITH_MASK)

    fg_mask = (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)

    # 연결 요소 중 마법사 본체 선택
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg_mask.astype(np.uint8))
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    main_char = (labels == largest_label)

    # 몸 내부의 모든 구멍 100% 채우기 (얼굴, 책, 가슴 등 완전 보존)
    main_char_filled = binary_fill_holes(main_char)

    # 잔여 좌측 사람 머리(x < 260, y > 350)와 우측 깃발(x > 580, y < 350) 강제 마스킹 제거
    main_char_filled[360:480, :260] = False
    main_char_filled[:340, 580:] = False

    # 부드러운 안티앨리어싱
    alpha = gaussian_filter(main_char_filled.astype(float), sigma=0.8)
    alpha = np.clip((alpha - 0.2) / 0.6, 0.0, 1.0) * 255.0

    im_rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:,:,:3] = im_rgb
    out[:,:,3] = np.uint8(alpha)

    Image.fromarray(out).save(out_png, "PNG", optimize=True)
    print("char_mage_unregistered.png processed successfully with ZERO holes!")

def main():
    print("=== Processing 3 Special Characters to Eliminate All Body Holes ===")
    process_plague_visitor()
    process_ghost_visitor()
    process_mage_unregistered()
    print("=== All 3 Special Characters Restored with ZERO Holes! ===")

if __name__ == "__main__":
    main()
