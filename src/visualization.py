"""
Visualization module for ASHIAN floor plan understanding system.
Implements Section 5 of the RSF Ventures assignment:
- View A: Original Blueprint View
- View B: Room Segmentation View (transparent overlays, crisp contours, centroid markers, area labels)
- View C: Door and Window Openings View (distinct markers + legend)
- View D: Combined Extraction View (comprehensive architectural overlay)
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import matplotlib.pyplot as plt

from src.config import VISUALIZATIONS_DIR


# Professional architectural color palette for distinct room identification
ROOM_PALETTE = [
    (52, 152, 219),   # Blue
    (46, 204, 113),   # Green
    (241, 196, 15),   # Yellow
    (231, 76, 60),    # Red
    (155, 89, 182),   # Purple
    (26, 188, 156),   # Turquoise
    (230, 126, 34),   # Orange
    (52, 73, 94),     # Navy Slate
    (149, 165, 166),  # Silver
    (243, 156, 18),   # Amber
    (39, 174, 96),    # Emerald
    (142, 68, 173),   # Dark Violet
    (211, 84, 0),     # Rust
    (192, 57, 43),    # Crimson
    (41, 128, 185),   # Cerulean
]


class FloorPlanVisualizer:
    """Generates rigorous, verified architectural visualizations from extracted data."""

    def __init__(self, output_dir: Path = VISUALIZATIONS_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_room_segmentation_view(
        self,
        image_rgb: np.ndarray,
        rooms: List[Dict],
        labeled_mask: np.ndarray,
        plan_id: int
    ) -> np.ndarray:
        """
        View B: Room Segmentation View.
        Uses actual segmentation mask pixels to draw semi-transparent colored overlays,
        crisp perimeter contours, centroid markers, room IDs, and pixel areas.
        """
        overlay = image_rgb.copy()
        H, W = overlay.shape[:2]
        scale = max(0.5, min(1.8, W / 1500.0))
        font = cv2.FONT_HERSHEY_SIMPLEX

        room_layer = np.zeros_like(image_rgb)

        for room in rooms:
            idx = room["room_index"]
            color = ROOM_PALETTE[(idx - 1) % len(ROOM_PALETTE)]

            # Mask of this exact room
            single_room_mask = (labeled_mask == idx).astype(np.uint8) * 255
            if np.count_nonzero(single_room_mask) == 0:
                continue

            # Fill actual room pixels with room color
            room_layer[single_room_mask > 0] = color

            # Extract exact outer perimeter contour
            contours, _ = cv2.findContours(single_room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(overlay, contours, -1, (20, 20, 20), max(2, int(3 * scale)))

        # Blend room layer with alpha 0.40 to keep underlying architectural drawing visible
        cv2.addWeighted(room_layer, 0.40, overlay, 0.60, 0, overlay)

        # Draw centroid badge, room ID, and area label
        for room in rooms:
            cx, cy = int(room["centroid_x"]), int(room["centroid_y"])
            area_str = f"{room['area_pixels']:,}px"
            lbl_line1 = f"Room {room['room_index']}"
            lbl_line2 = area_str

            font_scale = 0.50 * scale
            thick = max(1, int(1.5 * scale))

            # Compute badge size
            (w1, h1), b1 = cv2.getTextSize(lbl_line1, font, font_scale, thick)
            (w2, h2), b2 = cv2.getTextSize(lbl_line2, font, font_scale * 0.85, thick)
            bw = max(w1, w2) + 12
            bh = h1 + h2 + 14

            bx1 = max(0, min(W - bw, cx - bw // 2))
            by1 = max(0, min(H - bh, cy - bh // 2))

            # Rounded / solid badge
            cv2.rectangle(overlay, (bx1, by1), (bx1 + bw, by1 + bh), (255, 255, 255), -1)
            cv2.rectangle(overlay, (bx1, by1), (bx1 + bw, by1 + bh), (40, 40, 40), 1)

            # Centroid point
            cv2.circle(overlay, (cx, cy), max(3, int(4 * scale)), (220, 20, 20), -1)

            cv2.putText(overlay, lbl_line1, (bx1 + 6, by1 + h1 + 4), font, font_scale, (15, 15, 15), thick, cv2.LINE_AA)
            cv2.putText(overlay, lbl_line2, (bx1 + 6, by1 + h1 + h2 + 8), font, font_scale * 0.85, (70, 70, 70), 1, cv2.LINE_AA)

        return overlay

    def render_doors_windows_view(
        self,
        image_rgb: np.ndarray,
        doors: List[Dict],
        windows: List[Dict],
        plan_id: int
    ) -> np.ndarray:
        """
        View C: Door and Window Openings View.
        Draws doors in vibrant red-orange with 'D#' labels,
        and windows in golden amber with 'W#' labels.
        """
        overlay = image_rgb.copy()
        H, W = overlay.shape[:2]
        scale = max(0.5, min(1.8, W / 1500.0))
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Draw Doors
        for d in doors:
            dx, dy, dw, dh = d["bbox_x"], d["bbox_y"], d["bbox_width"], d["bbox_height"]
            dcx, dcy = int(d["centroid_x"]), int(d["centroid_y"])
            # Boundary box
            cv2.rectangle(overlay, (dx, dy), (dx + dw, dy + dh), (220, 50, 40), max(2, int(3 * scale)))
            # Door marker dot
            cv2.circle(overlay, (dcx, dcy), max(4, int(5 * scale)), (220, 50, 40), -1)

        # Draw Windows
        for w in windows:
            wx, wy, ww, wh = w["bbox_x"], w["bbox_y"], w["bbox_width"], w["bbox_height"]
            wcx, wcy = int(w["centroid_x"]), int(w["centroid_y"])
            # Boundary box
            cv2.rectangle(overlay, (wx, wy), (wx + ww, wy + wh), (245, 190, 20), max(2, int(3 * scale)))
            # Window marker dot
            cv2.circle(overlay, (wcx, wcy), max(4, int(5 * scale)), (245, 190, 20), -1)

        return overlay

    def create_combined_view(
        self,
        image_rgb: np.ndarray,
        rooms: List[Dict],
        doors: List[Dict],
        windows: List[Dict],
        labeled_mask: np.ndarray,
        plan_id: int,
        save_filename: Optional[str] = None
    ) -> np.ndarray:
        """
        View D: Combined Architectural Extraction View.
        Composite of Original Blueprint + Real Room Boundaries + Centroid Badges + Doors + Windows.
        """
        # Start with the room segmentation overlay
        combined = self.render_room_segmentation_view(image_rgb, rooms, labeled_mask, plan_id)
        H, W = combined.shape[:2]
        scale = max(0.5, min(1.8, W / 1500.0))

        # Overlay doors
        for d in doors:
            dx, dy, dw, dh = d["bbox_x"], d["bbox_y"], d["bbox_width"], d["bbox_height"]
            dcx, dcy = int(d["centroid_x"]), int(d["centroid_y"])
            cv2.rectangle(combined, (dx, dy), (dx + dw, dy + dh), (220, 40, 30), max(2, int(3 * scale)))
            cv2.circle(combined, (dcx, dcy), max(3, int(4 * scale)), (220, 40, 30), -1)

        # Overlay windows
        for w in windows:
            wx, wy, ww, wh = w["bbox_x"], w["bbox_y"], w["bbox_width"], w["bbox_height"]
            wcx, wcy = int(w["centroid_x"]), int(w["centroid_y"])
            cv2.rectangle(combined, (wx, wy), (wx + ww, wy + wh), (240, 185, 20), max(2, int(3 * scale)))
            cv2.circle(combined, (wcx, wcy), max(3, int(4 * scale)), (240, 185, 20), -1)

        # Add professional top banner with legend
        banner_h = max(45, int(55 * scale))
        banner = np.full((banner_h, W, 3), 248, dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.65 * scale
        thick = max(1, int(2 * scale))

        title_text = f"ASHIAN Plan {plan_id}  |  Rooms: {len(rooms)}  |  Doors: {len(doors)} (Red)  |  Windows: {len(windows)} (Yellow)"
        cv2.putText(banner, title_text, (int(20 * scale), int(35 * scale)), font, font_scale, (20, 20, 20), thick, cv2.LINE_AA)

        final_composite = np.vstack([banner, combined])

        if save_filename:
            out_path = self.output_dir / save_filename
            cv2.imwrite(str(out_path), cv2.cvtColor(final_composite, cv2.COLOR_RGB2BGR))

        return final_composite

    def generate_four_view_panel(
        self,
        image_rgb: np.ndarray,
        mask_rgb: np.ndarray,
        rooms: List[Dict],
        doors: List[Dict],
        windows: List[Dict],
        labeled_mask: np.ndarray,
        plan_id: int,
        save_filename: Optional[str] = None
    ) -> str:
        """
        Creates a side-by-side comparative inspection panel:
        [A] Original Blueprint | [B] Ground Truth Mask | [C] Extracted Rooms | [D] Combined Overlay
        """
        room_view = self.render_room_segmentation_view(image_rgb, rooms, labeled_mask, plan_id)
        openings_view = self.render_doors_windows_view(image_rgb, doors, windows, plan_id)
        combined_view = self.create_combined_view(image_rgb, rooms, doors, windows, labeled_mask, plan_id)

        fig, axes = plt.subplots(1, 4, figsize=(26, 7), dpi=150)
        
        axes[0].imshow(image_rgb)
        axes[0].set_title(f"A. Original Blueprint (Plan {plan_id})", fontsize=12, fontweight="bold")
        axes[0].axis("off")

        axes[1].imshow(mask_rgb)
        axes[1].set_title(f"B. Semantic Mask (Kaggle Dataset)", fontsize=12, fontweight="bold")
        axes[1].axis("off")

        axes[2].imshow(room_view)
        axes[2].set_title(f"C. Extracted Rooms ({len(rooms)} Regions)", fontsize=12, fontweight="bold")
        axes[2].axis("off")

        axes[3].imshow(combined_view)
        axes[3].set_title(f"D. Combined Extraction Overlay", fontsize=12, fontweight="bold")
        axes[3].axis("off")

        plt.tight_layout()
        if not save_filename:
            save_filename = f"plan_{plan_id}_audit_panel.png"
        out_path = self.output_dir / save_filename
        plt.savefig(str(out_path), bbox_inches="tight")
        plt.close(fig)
        return str(out_path)
