"""Pure OpenCV/numpy helpers used to clean up rasterized document pages.

This module deliberately has **no** PDF/OCR dependency (in particular it never
imports PyMuPDF): callers hand in plain numpy arrays and get arrays back, which
keeps every step individually testable and reusable for images loaded from disk
as well as for pages rasterized out of a PDF.

Conventions
-----------
* colour images are 8-bit BGR (OpenCV channel order);
* grayscale images are 2-D 8-bit ``uint8`` arrays;
* inputs are never modified in place — every function returns a new array.

The helpers are meant to run once per page ahead of Tesseract, so the cheap
steps (:func:`deskew`, :func:`enhance_contrast`) are always safe to call while
the expensive one (:func:`denoise`, non-local means) is left opt-in.
"""

from __future__ import annotations

import cv2
import numpy as np

#: Largest tilt (degrees) :func:`deskew` is willing to correct. A bigger value
#: is far more likely to be a mis-measured text block than a scanned page.
MAX_DESKEW_ANGLE = 15.0
#: Tilts below this many degrees are ignored: rotating for them only adds blur.
MIN_DESKEW_ANGLE = 0.1
#: CLAHE parameters. The OpenCV defaults (clip limit 40, 8x8 tiles) amplify
#: paper noise, so a mild clip limit is used instead.
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID = (8, 8)
#: Non-local-means filter strength for :func:`denoise`.
DENOISE_STRENGTH = 10.0


def to_gray(image: np.ndarray) -> np.ndarray:
    """Return a 2-D ``uint8`` grayscale copy of ``image``.

    Accepts grayscale (``HxW``), BGR (``HxWx3``) and BGRA (``HxWx4``) 8-bit
    arrays. The alpha channel is dropped via ``cv2.COLOR_BGRA2GRAY``; other
    dtypes/shapes raise ``ValueError`` so callers fail loudly instead of
    feeding garbage into the OCR engine.
    """
    if image is None:
        raise ValueError("to_gray() received None instead of an image array")
    if image.dtype != np.uint8:
        raise ValueError(f"to_gray() expects an 8-bit image, got dtype {image.dtype}")
    if image.ndim == 2:
        return image.copy()
    if image.ndim == 3 and image.shape[2] in (3, 4):
        code = cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY
        return cv2.cvtColor(image, code)
    raise ValueError(f"to_gray() does not support image shape {image.shape}")


def measure_tilt(gray: np.ndarray) -> float | None:
    """Estimate the page tilt in degrees from the position of the ink pixels.

    Ink is separated with Otsu's threshold, wrapped in ``cv2.minAreaRect`` and
    the rectangle angle is normalised into ``(-45, 45]``. The normalisation
    (``angle % 90``, then ``-90`` when the result is above 45) keeps working
    across OpenCV versions, which report the raw angle either in ``(-90, 0]``
    or in ``(0, 90]``. Positive values mean "rotate by that many degrees to
    straighten the page".

    Returns ``None`` when the page contains no ink at all (blank scan).
    """
    if gray.ndim != 2:
        raise ValueError(f"measure_tilt() expects a 2-D grayscale image, got {gray.shape}")
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ink_pixels = cv2.findNonZero(ink)
    if ink_pixels is None:
        return None
    angle = float(cv2.minAreaRect(ink_pixels)[-1]) % 90.0
    if angle > 45.0:
        angle -= 90.0
    return angle


def deskew(gray: np.ndarray, max_angle: float = MAX_DESKEW_ANGLE) -> np.ndarray:
    """Straighten a scanned page by rotating it about its centre.

    The tilt comes from :func:`measure_tilt`, is clamped to ``±max_angle``
    (anything wilder means the ink bounding box, not the paper, is skewed) and
    is skipped below :data:`MIN_DESKEW_ANGLE`. Border pixels are replicated, so
    content rotated slightly outside the original frame comes back intact
    rather than as a black wedge.
    """
    if gray.ndim != 2:
        raise ValueError(f"deskew() expects a 2-D grayscale image, got {gray.shape}")
    angle = measure_tilt(gray)
    if angle is None or abs(angle) < MIN_DESKEW_ANGLE:
        return gray.copy()
    angle = max(-max_angle, min(max_angle, angle))
    height, width = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2.0, height / 2.0), angle, 1.0)
    return cv2.warpAffine(
        gray,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def enhance_contrast(
    gray: np.ndarray,
    clip_limit: float = CLAHE_CLIP_LIMIT,
    tile_grid: tuple[int, int] = CLAHE_TILE_GRID,
) -> np.ndarray:
    """Apply CLAHE (adaptive histogram equalisation) to a grayscale page.

    Photocopied and camera-captured pages are usually washed out in some areas
    and dark in others; CLAHE equalises on a ``tile_grid`` of local windows so
    faint stamp/seal text survives without blowing out the bright regions.
    """
    if gray.ndim != 2:
        raise ValueError(f"enhance_contrast() expects a 2-D grayscale image, got {gray.shape}")
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tuple(tile_grid))
    return clahe.apply(gray)


def denoise(
    gray: np.ndarray,
    strength: float = DENOISE_STRENGTH,
    template_window: int = 7,
    search_window: int = 21,
) -> np.ndarray:
    """Non-local-means denoise for noisy scans.

    Kept optional on purpose: ``cv2.fastNlMeansDenoising`` costs seconds per
    300 dpi A4 page, and Tesseract's own binarisation already copes with light
    JPEG/speckle noise. Call it from the pipeline only for visibly dirty scans.
    """
    if gray.ndim != 2:
        raise ValueError(f"denoise() expects a 2-D grayscale image, got {gray.shape}")
    return cv2.fastNlMeansDenoising(
        gray, None, float(strength), int(template_window), int(search_window)
    )
