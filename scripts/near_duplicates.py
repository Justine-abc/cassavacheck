"""Near-duplicate check across the published split by Hamming distance between perceptual hashes, not only identical hashes.
Uses the 64-bit pHash (hash size 8) stored in data/split_v1_seed42.csv by notebook 01; reads no image, label-free apart from reporting the class of each pair.
Run: python scripts/near_duplicates.py --threshold 10
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SPLIT_PATH = Path("data/split_v1_seed42.csv")
CHECKED_DISTANCES = (0, 2, 4, 6, 8, 10, 12)


def hash_bits(hashes: pd.Series) -> np.ndarray:
    raw = np.frombuffer(b"".join(bytes.fromhex(h) for h in hashes), dtype=np.uint8).reshape(-1, 8)
    return np.unpackbits(raw, axis=1)


def nearest(bits: np.ndarray, query: np.ndarray, reference: np.ndarray, exclude_self: bool = False, chunk: int = 512):
    """For every query image, the Hamming distance to its nearest reference image and that image's row."""
    reference_bits = bits[reference]
    distances, rows = np.empty(len(query), dtype=int), np.empty(len(query), dtype=int)
    for start in range(0, len(query), chunk):
        block = query[start:start + chunk]
        hamming = (bits[block][:, None, :] != reference_bits[None, :, :]).sum(axis=2)
        if exclude_self:                      # an image is always at distance 0 from itself
            hamming[block[:, None] == reference[None, :]] = 99
        distances[start:start + chunk], rows[start:start + chunk] = hamming.min(axis=1), reference[hamming.argmin(axis=1)]
    return distances, rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=10, help="pairs at or below this many differing bits (of 64) are listed for visual inspection")
    parser.add_argument("--output", type=Path, default=Path("docs/near_duplicate_pairs.csv"))
    arguments = parser.parse_args()

    labels = pd.read_csv(SPLIT_PATH)
    bits = hash_bits(labels["phash"])
    rows_of = {name: np.flatnonzero(labels["split"].values == name) for name in ("train", "validation", "test")}

    print(f"{len(labels)} images, 64-bit pHash, Hamming distance = number of differing bits")
    pairs = []
    for query, reference in (("validation", "train"), ("test", "train"), ("test", "validation")):
        distances, nearest_rows = nearest(bits, rows_of[query], rows_of[reference])
        counts = ", ".join(f"<= {d}: {int((distances <= d).sum())}" for d in CHECKED_DISTANCES)
        print(f"{query} vs nearest {reference}: closest {distances.min()} | {counts}")
        for row, other, distance in zip(rows_of[query], nearest_rows, distances):
            if distance <= arguments.threshold:
                pairs.append({"hamming": int(distance), "image_id": labels.image_id[row], "split": query, "class": labels["class"][row],
                              "nearest_image_id": labels.image_id[other], "nearest_split": reference, "nearest_class": labels["class"][other]})

    everyone = np.arange(len(labels))
    distances, _ = nearest(bits, everyone, everyone, exclude_self=True)
    print("whole dataset, nearest other image: " + ", ".join(f"<= {d}: {int((distances <= d).sum())}" for d in CHECKED_DISTANCES))
    print(f"typical spacing: median {np.median(distances):.0f} bits, 1st percentile {np.percentile(distances, 1):.0f}, 5th percentile {np.percentile(distances, 5):.0f}")

    table = pd.DataFrame(pairs).sort_values(["hamming", "image_id"])
    table.to_csv(arguments.output, index=False)
    same = int((table["class"] == table["nearest_class"]).sum())
    print(f"{len(table)} cross-split pairs within {arguments.threshold} bits ({same} with the same class) saved to {arguments.output} for visual inspection")
