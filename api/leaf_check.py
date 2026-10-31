"""Input check before the classifier: is there enough plant colour in the photo to be a leaf? It never changes a diagnosis;
it only refuses photos that are clearly not a leaf (a screenshot, a wall, a face), which the classifier would otherwise score."""
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from torchvision import transforms

# Same crop the classifier sees, so the check judges the pixels the model would judge.
_crop = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224)])

# Plant colour in HSV: hue from yellow to green (35 to 165 degrees), so yellow mosaic and pale leaves still count,
# with enough saturation and brightness to exclude grey, white and black. Fixed by hand, not tuned on any split.
HUE_RANGE_DEGREES = (35, 165)
MIN_SATURATION = 0.15
MIN_VALUE = 0.12


def plant_fraction(image: Image.Image) -> float:
    """Share of pixels in the centre crop that have plant colour, between 0 and 1."""
    hsv = np.asarray(_crop(image.convert("RGB")).convert("HSV")).astype(np.float32)
    hue, saturation, value = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    plant = (hue >= HUE_RANGE_DEGREES[0]) & (hue <= HUE_RANGE_DEGREES[1]) & (saturation >= MIN_SATURATION) & (value >= MIN_VALUE)
    return float(plant.mean())


@dataclass(frozen=True)
class LeafCheck:
    """Rejects a photo whose plant fraction is below a cut-off measured on validation leaves (notebook 06)."""
    min_plant_fraction: float
    fitted_on: str

    @classmethod
    def load(cls, path: Path) -> "LeafCheck":
        """Without models/leaf_check.json the check is off (cut-off 0) and says so, as the calibration loader does."""
        if not path.exists():
            return cls(min_plant_fraction=0.0, fitted_on="none: leaf_check.json not found, check disabled")
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(min_plant_fraction=float(raw["min_plant_fraction"]), fitted_on=str(raw.get("fitted_on", "unknown")))

    def looks_like_leaf(self, image: Image.Image) -> bool:
        return plant_fraction(image) >= self.min_plant_fraction
