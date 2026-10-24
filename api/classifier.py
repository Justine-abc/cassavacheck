"""Image classifiers. The abstract base fixes the contract (an image in, five logits out) so the API never depends on one backbone."""
from abc import ABC, abstractmethod
from pathlib import Path

import torch
import torchvision
from PIL import Image
from torchvision import transforms

from api.config import CLASS_NAMES


class ImageClassifier(ABC):
    """Contract for any backbone: load weights once, turn a PIL image into a vector of logits."""

    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    def __init__(self, weights_path: Path):
        self.weights_path = weights_path
        self.weights_loaded = weights_path.exists()
        self.network = self.build_network()
        if self.weights_loaded:
            # map_location keeps this usable on a CPU-only server even though training ran on a GPU
            self.network.load_state_dict(torch.load(weights_path, map_location="cpu"))
        self.network.eval()

    @abstractmethod
    def build_network(self) -> torch.nn.Module:
        """Return the backbone with its head replaced by a 5-way layer; weights are loaded by the base class."""

    @property
    def name(self) -> str:
        return type(self).__name__

    def predict_logits(self, image: Image.Image) -> torch.Tensor:
        batch = self.preprocess(image.convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            return self.network(batch)[0]


class MobileNetV3Classifier(ImageClassifier):
    """MobileNetV3-Large, the lightweight backbone chosen for CPU latency (about 4.2 million parameters)."""

    def build_network(self) -> torch.nn.Module:
        network = torchvision.models.mobilenet_v3_large(weights=None)
        network.classifier[-1] = torch.nn.Linear(network.classifier[-1].in_features, len(CLASS_NAMES))
        return network


class ResNet18Classifier(ImageClassifier):
    """ResNet-18, the second baseline of the proposal; same contract, different backbone."""

    def build_network(self) -> torch.nn.Module:
        network = torchvision.models.resnet18(weights=None)
        network.fc = torch.nn.Linear(network.fc.in_features, len(CLASS_NAMES))
        return network
