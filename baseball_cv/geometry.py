"""Field-coordinate geometry helpers.

Field convention: origin at home plate, +x toward the 1B/3B axis (positive = 1B side),
+y pointing toward center field. Distances are in feet.
"""
from __future__ import annotations

import numpy as np

BASE_DISTANCE_FT = 90.0
_OFFSET = BASE_DISTANCE_FT / np.sqrt(2)

HOME = np.array([0.0, 0.0])
FIRST = np.array([_OFFSET, _OFFSET])
SECOND = np.array([0.0, 2 * _OFFSET])
THIRD = np.array([-_OFFSET, _OFFSET])

BASES_FT = np.stack([HOME, FIRST, SECOND, THIRD])


def homography_from_bases(home_px, first_px, second_px, third_px):
    """Pixel coords of the four bases -> homography mapping pixels to field feet."""
    import cv2

    src = np.array([home_px, first_px, second_px, third_px], dtype=np.float32)
    dst = np.array([HOME, FIRST, SECOND, THIRD], dtype=np.float32)
    H, _ = cv2.findHomography(src, dst)
    return H


def apply_homography(H, pts_px):
    """Apply a homography to an (N, 2) array of pixel points."""
    import cv2

    pts = np.asarray(pts_px, dtype=np.float32).reshape(-1, 1, 2)
    out = cv2.perspectiveTransform(pts, H)
    return out.reshape(-1, 2)
