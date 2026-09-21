import sys
import os
from PIL import Image

def make_transparent(input_path, output_path, threshold=40):
    img = Image.open(input_path).convert("RGBA")
    w, h = img.size
    
    # 4개 모서리 픽셀 색상 샘플링하여 배경색 자동 보정
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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Saved transparent image to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        thresh = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        make_transparent(sys.argv[1], sys.argv[2], threshold=thresh)
    else:
        print("Usage: python make_transparent.py input_file output_file [threshold]")
