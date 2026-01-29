import os
from PIL import Image

def fix_checkerboard(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    pix = img.load()

    # Sample corners to find the background pattern
    # We'll assume the background is in the corners.
    bg_samples = []
    for x in [0, width-1]:
        for y in [0, height-1]:
            bg_samples.append(pix[x,y])
    
    # Simple strategy: anything close to neutral grey/black/white is probably background
    # unless it has significant saturation.
    new_img = Image.new("RGBA", (width, height), (0,0,0,0))
    new_pix = new_img.load()

    for x in range(width):
        for y in range(height):
            r, g, b, a = pix[x, y]
            
            # Distance from pure grey
            avg = (r + g + b) // 3
            dist_from_grey = abs(r-avg) + abs(g-avg) + abs(b-avg)
            
            # If it's very neutral (dist_from_grey < threshold) AND it's not too bright/dark
            # or if it's very close to one of the sampled corner colors.
            # Checkerboards often have colors like (200,200,200) and (230,230,230)
            
            is_bg = False
            if dist_from_grey < 15: # Highly neutral
                if avg < 50 or avg > 150: # Dark or Light grey
                    # To be safe, also check if it's "mostly" background
                    is_bg = True
            
            # Check against sampled corner colors
            for sr, sg, sb, sa in bg_samples:
                if abs(r-sr) < 10 and abs(g-sg) < 10 and abs(b-sb) < 10:
                    is_bg = True
                    break

            if not is_bg:
                new_pix[x, y] = (r, g, b, 255)
            else:
                new_pix[x, y] = (0, 0, 0, 0)

    new_img.save(output_path, "PNG")

input_path = "/home/jandro/.gemini/antigravity/brain/c05f7037-b5ce-4d8b-a987-76b85e45d152/storage_icon_1769633752265.png"
output_path = "/home/jandro/arcoverlay/Images/build_icons/storage.png"

if os.path.exists(input_path):
    fix_checkerboard(input_path, output_path)
    print("Fixed storage icon.")
else:
    print("Input not found.")
