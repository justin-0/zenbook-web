from PIL import Image
import torch
from torchvision import transforms, models
import os

# ==== Configuration ====
MODEL_PATH = r"C:\viloncedetection\vilonce_detection\vilonce_detection\violence_model.pth"      # Trained model file
IMAGE_PATH = r"C:\viloncedetection\vilonce_detection\vilonce_detection\dataset\train\vulgar\train2 (12).jpg"                # Image to test (put test.jpg in same folder or update the path)

# ==== Load model ====
def load_model(model_path, device):
    checkpoint = torch.load(model_path, map_location=device)
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.fc = torch.nn.Linear(model.fc.in_features, len(checkpoint['classes']))
    model.load_state_dict(checkpoint['model_state'])
    model = model.to(device)
    model.eval()
    return model, checkpoint['classes']

# ==== Preprocess image ====
def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert("RGB")
    return transform(image).unsqueeze(0)  # Add batch dimension

# ==== Prediction ====
def predict(model, image_tensor, device, class_names):
    with torch.no_grad():
        image_tensor = image_tensor.to(device)
        output = model(image_tensor)
        pred_idx = torch.argmax(output, dim=1).item()
        return class_names[pred_idx]

# ==== Main function ====
def main():
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found: {IMAGE_PATH}")
        return
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found: {MODEL_PATH}")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, class_names = load_model(MODEL_PATH, device)
    image_tensor = preprocess_image(IMAGE_PATH)
    result = predict(model, image_tensor, device, class_names)

    print(f"✅ Prediction: {result}")

if __name__ == "__main__":
    main()
