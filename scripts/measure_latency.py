"""Measure the forward-pass latency the proposal defines: one 224x224 image, batch size 1, one CPU thread, median of 100 runs after warm-up.
Run: python scripts/measure_latency.py --runs 100
"""
import argparse
import platform
import statistics
import time

import torch
from PIL import Image

from api import config
from api.classifier import MobileNetV3Classifier, ResNet18Classifier


def measure(classifier, runs: int) -> dict:
    image = Image.new("RGB", (800, 600), (60, 140, 50))
    for _ in range(10):                       # warm-up: first calls pay for lazy initialisation and are not representative
        classifier.predict_logits(image)
    timings = []
    for _ in range(runs):
        started = time.perf_counter()
        classifier.predict_logits(image)
        timings.append((time.perf_counter() - started) * 1000)
    return {"median_ms": round(statistics.median(timings), 1), "p95_ms": round(sorted(timings)[int(0.95 * runs) - 1], 1), "runs": runs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--threads", type=int, default=1, help="CPU threads; 1 reproduces the proposal's one-core boundary")
    arguments = parser.parse_args()
    torch.set_num_threads(arguments.threads)
    print(f"machine: {platform.processor() or platform.machine()} | {platform.system()} {platform.release()} | torch {torch.__version__} | threads {arguments.threads}")
    print("MobileNetV3-Large:", measure(MobileNetV3Classifier(config.WEIGHTS_PATH), arguments.runs))
    print("ResNet-18 (random weights, architecture cost only):", measure(ResNet18Classifier(config.MODELS_DIRECTORY / "resnet18_baseline.pt"), arguments.runs))
