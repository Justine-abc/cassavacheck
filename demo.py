import sys
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

CLASSES = ["CBB", "CBSD", "CGM", "CMD", "healthy"]
DISEASE_INFO = {
    "CBB": "Cassava Bacterial Blight - Angular leaf lesions and systemic wilting.",
    "CBSD": "Cassava Brown Streak Disease - Severe feathery chlorosis and root necrosis.",
    "CGM": "Cassava Green Mite - Yellow speckling, mottled appearance, and leaf shoe-stringing.",
    "CMD": "Cassava Mosaic Disease - Severe mosaic distortion and stunted plant development.",
    "healthy": "Healthy Tissue - No significant disease symptoms identified."
}

device = torch.device("cpu")
model = models.mobilenet_v3_small(weights=None)
in_features = model.classifier[3].in_features
model.classifier[3] = nn.Linear(in_features, len(CLASSES))

weights_path = Path("models/mobilenetv3_baseline.pt")
if not weights_path.exists():
    print(f"Error: Could not find weights file at {weights_path}")
    sys.exit(1)

model.load_state_dict(torch.load(weights_path, map_location=device))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def diagnose(image_path: str):
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error reading image: {e}")
        return

    tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        confidence, pred_idx = torch.max(probs, dim=0)

    predicted_label = CLASSES[pred_idx.item()]
    print("\n" + "=" * 55)
    print("           CASSACHECK LOCAL INFERENCE           ")
    print("=" * 55)
    print(f"File Tested : {image_path}")
    print(f"Diagnosis   : {predicted_label} ({confidence.item() * 100:.2f}% confidence)")
    print(f"Overview    : {DISEASE_INFO[predicted_label]}")
    print("\nClass Probabilities:")
    for label, prob in zip(CLASSES, probs):
        print(f"  - {label:<8}: {prob.item() * 100:6.2f}%")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        diagnose(sys.argv[1])
    else:
        print("Usage: python3 demo.py <path_to_leaf_image.jpg>")
