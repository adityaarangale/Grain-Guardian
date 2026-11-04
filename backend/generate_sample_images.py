"""
generate_sample_images.py
Generates realistic grain sample images for demo testing of the Grain Guardian
Optical Contamination & Seed Health Scanner.

Samples generated:
1. healthy_wheat.jpg       - Clean, uniform golden wheat grains, sound kernels, 0% BGYF.
2. aflatoxin_bgyf.jpg      - 365nm UV excitation showing bright greenish-yellow fluorescence (BGYF) from Aspergillus flavus.
3. mold_damaged.jpg        - Visible black/grey fungal rot, discolored kernels, and mold mycelium spots.
4. borderline_suspect.jpg  - Borderline sample with isolated fluorescent specks (~2.8% BGYF) and mild discoloration.
"""

import os
import cv2
import numpy as np

def create_grain_texture(w=700, h=520, bg_color=(22, 24, 20)):
    """Creates a base inspection tray with subtle textured lighting."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = bg_color
    # Subtle vignette and gradient
    center_x, center_y = w // 2, h // 2
    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    max_dist = np.sqrt(center_x**2 + center_y**2)
    vignette = 1.0 - 0.25 * (dist_from_center / max_dist)
    for c in range(3):
        img[:, :, c] = np.clip(img[:, :, c] * vignette, 0, 255).astype(np.uint8)
    return img

def draw_realistic_grain(img, cx, cy, length=24, width=13, angle=0, base_bgr=(65, 160, 215), is_broken=False):
    """Draws a wheat kernel with organic shading and ventral crease."""
    overlay = np.zeros_like(img)
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Kernel body
    axes = (length, width) if not is_broken else (int(length * 0.65), int(width * 0.9))
    cv2.ellipse(mask, (cx, cy), axes, angle, 0, 360, 255, -1)
    
    # Kernel color variation
    color = [
        int(np.clip(base_bgr[0] + np.random.randint(-10, 10), 10, 255)),
        int(np.clip(base_bgr[1] + np.random.randint(-15, 15), 10, 255)),
        int(np.clip(base_bgr[2] + np.random.randint(-15, 15), 10, 255))
    ]
    overlay[mask > 0] = color
    
    # Add dorsal highlight (lighter amber center)
    rad_rad = int(width * 0.6)
    hl_color = [min(255, c + 35) for c in color]
    cv2.circle(overlay, (cx, cy), rad_rad, hl_color, -1)
    
    # Blend overlay into image
    cv2.ellipse(img, (cx, cy), axes, angle, 0, 360, color, -1)
    
    # Central crease characteristic of wheat kernel
    rad = np.radians(angle)
    dx = int((length - 4) * np.cos(rad))
    dy = int((length - 4) * np.sin(rad))
    crease_color = [max(0, c - 50) for c in color]
    cv2.line(img, (cx - dx, cy - dy), (cx + dx, cy + dy), crease_color, 1, cv2.LINE_AA)
    
    # Edge shadow
    cv2.ellipse(img, (cx, cy), axes, angle, 0, 360, crease_color, 1, cv2.LINE_AA)

def generate_healthy_wheat():
    np.random.seed(101)
    img = create_grain_texture(700, 520, bg_color=(20, 22, 19))
    
    # Scatter 90 healthy wheat grains
    for _ in range(95):
        cx = np.random.randint(60, 640)
        cy = np.random.randint(50, 470)
        length = np.random.randint(18, 26)
        width = np.random.randint(9, 14)
        angle = np.random.randint(0, 180)
        # Golden wheat amber in BGR
        base_bgr = (50, 155, 215)
        draw_realistic_grain(img, cx, cy, length, width, angle, base_bgr)
    
    # Add subtle image noise for natural camera realism
    noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def generate_aflatoxin_bgyf():
    """Generates 365nm UV excitation frame with high BGYF fluorescence clusters."""
    np.random.seed(202)
    # Deep violet/ultraviolet darkfield chamber background
    img = create_grain_texture(700, 520, bg_color=(32, 12, 22))
    
    # Draw wheat kernels in dark UV silhouette (deep purplish-gray)
    grain_positions = []
    for _ in range(90):
        cx = np.random.randint(60, 640)
        cy = np.random.randint(50, 470)
        length = np.random.randint(18, 25)
        width = np.random.randint(9, 13)
        angle = np.random.randint(0, 180)
        grain_positions.append((cx, cy))
        draw_realistic_grain(img, cx, cy, length, width, angle, base_bgr=(60, 35, 48))
    
    # Prominent Aflatoxin BGYF (Bright Greenish-Yellow Fluorescence)
    # High luminous yellow-green emission under 365nm UV excitation (Aspergillus flavus)
    # BGR for neon greenish-yellow: (30, 245, 210), (10, 255, 190)
    for _ in range(12):
        # Pick near one of the grain positions
        parent_idx = np.random.randint(0, len(grain_positions))
        gx, gy = grain_positions[parent_idx]
        fx = gx + np.random.randint(-6, 7)
        fy = gy + np.random.randint(-6, 7)
        radius = np.random.randint(14, 24)
        
        # Outer soft glow halo
        cv2.circle(img, (fx, fy), radius + 8, (15, 160, 140), -1, cv2.LINE_AA)
        # Intense fluorescent core
        cv2.circle(img, (fx, fy), radius, (30, 240, 215), -1, cv2.LINE_AA)
        cv2.circle(img, (fx, fy), int(radius * 0.6), (10, 255, 235), -1, cv2.LINE_AA)
        # Center peak luminescence
        cv2.circle(img, (fx, fy), int(radius * 0.3), (80, 255, 250), -1, cv2.LINE_AA)

    # A few smaller fluorescent satellite specks
    for _ in range(8):
        fx = np.random.randint(80, 620)
        fy = np.random.randint(60, 460)
        cv2.circle(img, (fx, fy), np.random.randint(4, 8), (25, 220, 195), -1, cv2.LINE_AA)

    noise = np.random.normal(0, 4, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def generate_mold_damaged():
    """Generates wheat sample with visible mold/fungal blemishes, blackened germ, and shriveled grains."""
    np.random.seed(303)
    img = create_grain_texture(700, 520, bg_color=(20, 22, 19))
    
    grain_positions = []
    for i in range(95):
        cx = np.random.randint(60, 640)
        cy = np.random.randint(50, 470)
        length = np.random.randint(16, 25)
        width = np.random.randint(8, 14)
        angle = np.random.randint(0, 180)
        is_damaged = (i % 4 == 0) # 25% show visible mold or rot
        is_broken = (i % 7 == 0)
        
        if is_damaged:
            # Dull discolored brownish-gray base
            base_bgr = (40, 75, 95)
        else:
            base_bgr = (50, 155, 215)
            
        draw_realistic_grain(img, cx, cy, length, width, angle, base_bgr, is_broken=is_broken)
        grain_positions.append((cx, cy, is_damaged))

    # Add dark black fungal lesions / mycelium rot spots on damaged grains
    for (cx, cy, is_damaged) in grain_positions:
        if is_damaged:
            # Black rot / Karnal bunt / Black point defect
            for _ in range(np.random.randint(2, 4)):
                lx = cx + np.random.randint(-8, 9)
                ly = cy + np.random.randint(-8, 9)
                rad = np.random.randint(4, 9)
                # Dark charcoal/black fungal rot
                cv2.circle(img, (lx, ly), rad, (15, 15, 18), -1, cv2.LINE_AA)
                # Fuzzy mycelium margin (greyish)
                cv2.circle(img, (lx, ly), rad + 2, (75, 80, 78), 1, cv2.LINE_AA)

    noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def generate_borderline_suspect():
    """Generates a borderline grain sample with low-to-moderate fluorescence (suspect ~2.5-3.0%)."""
    np.random.seed(404)
    img = create_grain_texture(700, 520, bg_color=(28, 16, 22))
    
    grain_positions = []
    for _ in range(90):
        cx = np.random.randint(60, 640)
        cy = np.random.randint(50, 470)
        length = np.random.randint(18, 24)
        width = np.random.randint(9, 13)
        angle = np.random.randint(0, 180)
        grain_positions.append((cx, cy))
        draw_realistic_grain(img, cx, cy, length, width, angle, base_bgr=(55, 60, 85))

    # 4 moderate fluorescent spots (Suspect range: 1.5% - 4.0%)
    for _ in range(4):
        parent_idx = np.random.randint(0, len(grain_positions))
        gx, gy = grain_positions[parent_idx]
        fx = gx + np.random.randint(-4, 5)
        fy = gy + np.random.randint(-4, 5)
        rad = np.random.randint(10, 16)
        cv2.circle(img, (fx, fy), rad + 4, (20, 150, 130), -1, cv2.LINE_AA)
        cv2.circle(img, (fx, fy), rad, (30, 230, 200), -1, cv2.LINE_AA)
        cv2.circle(img, (fx, fy), int(rad * 0.4), (60, 255, 230), -1, cv2.LINE_AA)

    noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_samples_dir = os.path.join(base_dir, "assets", "samples")
    uploads_samples_dir = os.path.join(base_dir, "backend", "uploads", "sample_images")
    
    os.makedirs(assets_samples_dir, exist_ok=True)
    os.makedirs(uploads_samples_dir, exist_ok=True)
    
    samples = {
        "healthy_wheat_sample.jpg": generate_healthy_wheat(),
        "aflatoxin_bgyf_sample.jpg": generate_aflatoxin_bgyf(),
        "mold_damaged_sample.jpg": generate_mold_damaged(),
        "suspect_borderline_sample.jpg": generate_borderline_suspect()
    }
    
    for filename, img in samples.items():
        p1 = os.path.join(assets_samples_dir, filename)
        p2 = os.path.join(uploads_samples_dir, filename)
        cv2.imwrite(p1, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        cv2.imwrite(p2, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"Generated sample: {filename} -> {os.path.getsize(p1)} bytes")

if __name__ == "__main__":
    main()

