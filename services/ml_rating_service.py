import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os

# Define the path to the pre-trained model weights
MODEL_WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "media", "ml_models", "nima_dense121.pt"
)

# Global variable to store the loaded model
_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model

    # Initialize a pre-trained DenseNet121 model
    # The pretrained=True loads ImageNet weights
    model_ft = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)

    # Replace the classifier layer for NIMA's 10-class output (scores 1-10)
    # The original paper uses a linear layer followed by softmax for probabilities.
    # The output is a distribution over 10 scores (1-10).
    num_ftrs = model_ft.classifier.in_features
    model_ft.classifier = nn.Sequential(
        nn.Linear(num_ftrs, 10),
        nn.Softmax(dim=1) # Output a probability distribution over scores 1-10
    )

    # Load the custom-trained NIMA weights
    if not os.path.exists(MODEL_WEIGHTS_PATH):
        raise FileNotFoundError(f"Model weights not found at {MODEL_WEIGHTS_PATH}. Please ensure the model is downloaded.")
    
    # Load state dict, but handle if it was saved with DataParallel
    state_dict = torch.load(MODEL_WEIGHTS_PATH, map_location=torch.device('cpu'))
    # Remove 'module.' prefix if saved with DataParallel
    new_state_dict = {}
    for k, v in state_dict.items():
        if k.startswith('module.'):
            new_state_dict[k[7:]] = v
        else:
            new_state_dict[k] = v

    model_ft.load_state_dict(new_state_dict)

    # Set model to evaluation mode
    model_ft.eval()
    _model = model_ft
    return _model

def _preprocess_image(image_path: str):
    """
    Preprocesses an image for the NIMA model.
    The NIMA model expects images resized to 224x224, normalized.
    """
    # Standard image transformations for DenseNet/ImageNet
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    img = Image.open(image_path).convert("RGB")
    img_tensor = transform(img)
    # Add batch dimension
    return img_tensor.unsqueeze(0)

def compute_ml_score(image_path: str) -> int:
    """
    Computes an aesthetic score for an image using the NIMA model.
    Returns an integer score between 1 and 10.
    """
    model = _load_model()
    image_tensor = _preprocess_image(image_path)

    with torch.no_grad():
        output = model(image_tensor)

    # The output is a probability distribution over scores 1-10.
    # To get a single score, we compute the expected value.
    # Scores are 1-indexed (1 to 10), so we multiply by (idx + 1).
    scores = torch.arange(1, 11).float()
    predicted_score = (output * scores).sum().item()

    # Round to the nearest integer and ensure it's within 1-10 range
    return int(round(predicted_score))