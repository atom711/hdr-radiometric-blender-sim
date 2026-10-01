import numpy as np
import matplotlib.pyplot as plt

def generate_high_contrast_target_scene(width=512, height=512):
    """
    Generates a high-contrast synthetic image containing a very bright target
    (like a laser or direct sun) and a dark, underexposed shadow zone.
    """
    scene = np.zeros((height, width), dtype=np.float64)
    
    # Establish a baseline ambient gradient across the matrix panel
    y, x = np.indices((height, width))
    scene += (x / width) * 100.0 + 30.0
    
    # Inject a deep, dark shadow target corridor (low photon return)
    scene[300:450, 50:200] = 5.0
    
    # Inject an intense, localized high-light emitter core
    yy, xx = np.ogrid[:height, :width]
    emitter_mask = (yy - 150)**2 + (xx - 380)**2 < 65**2
    scene[emitter_mask] = 800.0 # Exceeds standard 8-bit dynamic ceilings
    
    return scene

def simulate_sensor_exposures(base_scene):
    """
    Simulates capturing the physical scene at three distinct exposure steps.
    Enforces standard 8-bit hardware dynamic range clipping bounds (0 - 255).
    """
    short_exp = np.clip(base_scene * 0.25, 0, 255).astype(np.uint8)
    med_exp = np.clip(base_scene * 1.0, 0, 255).astype(np.uint8)
    long_exp = np.clip(base_scene * 4.0, 0, 255).astype(np.uint8)
    return short_exp, med_exp, long_exp

def calculate_gaussian_weights(intensity_matrix, sigma=40.0):
    """
    Calculates a radiometric health score for every pixel using a Gaussian curve.
    Crucial fix: Hard-clips weights to 0 for any sensor element that hits
    absolute hardware floor (0) or saturation ceiling (255).
    """
    center = 127.5
    weight = np.exp(-((intensity_matrix.astype(np.float64) - center) ** 2) / (2.0 * sigma ** 2))
    
    # Force weights to zero for broken/clipped data points
    weight[intensity_matrix <= 1] = 0.0
    weight[intensity_matrix >= 254] = 0.0
    return weight

def execute_radiometric_blend(short_frame, med_frame, long_frame):
    """
    Fuses multi-exposure frames into a single radiometrically balanced matrix
    using a weighted normalization blending array.
    """
    w_short = calculate_gaussian_weights(short_frame)
    w_med = calculate_gaussian_weights(med_frame)
    w_long = calculate_gaussian_weights(long_frame)
    
    sum_weights = w_short + w_med + w_long + 1e-6
    
    norm_short = short_frame.astype(np.float64) / 0.25
    norm_med = med_frame.astype(np.float64) / 1.0
    norm_long = long_frame.astype(np.float64) / 4.0
    
    # Linear mathematical combination matrix
    hdr_matrix = (norm_short * w_short + norm_med * w_med + norm_long * w_long) / sum_weights
    
    return hdr_matrix, w_long

# =====================================================================
# 📊 AUTOMATED RADIOMETRIC LABORATORY DISPLAY DASHBOARD
# =====================================================================
width, height = 512, 512
raw_scene = generate_high_contrast_target_scene(width, height)
img_short, img_med, img_long = simulate_sensor_exposures(raw_scene)

fused_hdr, long_weight_map = execute_radiometric_blend(img_short, img_med, img_long)

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
fig.suptitle("Multi-Exposure HDR Radiometric Blending Simulation", fontsize=13, fontweight='bold')

# Panel 1: Short Exposure (Highlight Optimized)
im1 = axes[0, 0].imshow(img_short, cmap='gray', vmin=0, vmax=255)
axes[0, 0].set_title("1. Short Exposure (Bright Object Visible)")
fig.colorbar(im1, ax=axes[0, 0], fraction=0.046, pad=0.04)

# Panel 2: Long Exposure (Shadow Optimized)
im2 = axes[0, 1].imshow(img_long, cmap='gray', vmin=0, vmax=255)
axes[0, 1].set_title("2. Long Exposure (Dark Object Visible)")
fig.colorbar(im2, ax=axes[0, 1], fraction=0.046, pad=0.04)

# Panel 3: Long Exposure Weight Map Distribution Matrix
im3 = axes[1, 0].imshow(long_weight_map, cmap='jet', vmin=0, vmax=1)
axes[1, 0].set_title("3. Long Exposure Mask")
fig.colorbar(im3, ax=axes[1, 0], fraction=0.046, pad=0.04)

# Panel 4: Final Corrected, Blended HDR Image
im4 = axes[1, 1].imshow(fused_hdr, cmap='gray')
axes[1, 1].set_title("4. Final Blended HDR Matrix")
fig.colorbar(im4, ax=axes[1, 1], fraction=0.046, pad=0.04)

plt.tight_layout()
plt.savefig("projects/hdr_radiometric_blender/hdr_radiometric_blender_plot.png", dpi=300)
plt.show()
