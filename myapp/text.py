# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, accuracy_score
# from transformers import BertTokenizer, BertForSequenceClassification
# from transformers import get_linear_schedule_with_warmup
# from torch.optim import AdamW
# import torch
# from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
# from tqdm import tqdm
#
#
# # 1. Load and clean the dataset
# def load_and_clean_data(filepath):
#     df = pd.read_csv('D:\\RISS 2025-26\\Cyber_Safe_Social_media\\Cyber_safe_Project\\Cyber_Safe_Social_Media\\sentiment_dataset.csv')
#
#     # Check for and handle NaN values
#     print(f"Before cleaning - Total rows: {len(df)}")
#     print(f"NaN values in text column: {df['text'].isna().sum()}")
#
#     # Drop rows with NaN values in text column
#     df = df.dropna(subset=['text'])
#
#     # Fill any remaining NaN in sentiment with 'neutral'
#     df['sentiment'] = df['sentiment'].fillna('neutral')
#
#     print(f"After cleaning - Total rows: {len(df)}")
#     return df
#
#
# # Load and clean the data
# df = load_and_clean_data(
#     'D:\\RISS 2025-26\\Cyber_Safe_Social_media\\Cyber_safe_Project\\Cyber_Safe_Social_Media\\sentiment_dataset.csv')
#
# # 2. Map sentiments to numerical values
# sentiment_map = {'positive': 0, 'neutral': 1, 'negative': 2}
# df['label'] = df['sentiment'].map(sentiment_map)
#
# # Check class distribution
# print("\nClass distribution:")
# print(df['sentiment'].value_counts())
#
# # 3. Split data into train and validation sets
# train_texts, val_texts, train_labels, val_labels = train_test_split(
#     df['text'].astype(str),  # Ensure all texts are strings
#     df['label'],
#     test_size=0.2,
#     random_state=42,
#     stratify=df['label']
# )
#
# # 4. Initialize BERT tokenizer
# tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
#
#
# # 5. Tokenize and encode the texts with improved error handling
# def encode_texts(texts):
#     input_ids = []
#     attention_masks = []
#
#     for text in texts:
#         try:
#             encoded = tokenizer.encode_plus(
#                 str(text),  # Ensure text is string
#                 add_special_tokens=True,
#                 max_length=128,
#                 padding='max_length',
#                 truncation=True,
#                 return_attention_mask=True,
#                 return_tensors='pt'
#             )
#             input_ids.append(encoded['input_ids'])
#             attention_masks.append(encoded['attention_mask'])
#         except Exception as e:
#             print(f"Error encoding text: {text}")
#             print(f"Error: {e}")
#             # Fallback to empty encoding
#             empty_encoding = tokenizer.encode_plus(
#                 "",
#                 add_special_tokens=True,
#                 max_length=128,
#                 padding='max_length',
#                 truncation=True,
#                 return_attention_mask=True,
#                 return_tensors='pt'
#             )
#             input_ids.append(empty_encoding['input_ids'])
#             attention_masks.append(empty_encoding['attention_mask'])
#
#     return torch.cat(input_ids, dim=0), torch.cat(attention_masks, dim=0)
#
#
# print("\nEncoding training texts...")
# train_input_ids, train_attention_masks = encode_texts(train_texts)
# print("Encoding validation texts...")
# val_input_ids, val_attention_masks = encode_texts(val_texts)
#
# # 6. Convert labels to tensors
# train_labels = torch.tensor(train_labels.values)
# val_labels = torch.tensor(val_labels.values)
#
# # 7. Create DataLoader
# batch_size = 32
#
# train_dataset = TensorDataset(train_input_ids, train_attention_masks, train_labels)
# train_sampler = RandomSampler(train_dataset)
# train_dataloader = DataLoader(train_dataset, sampler=train_sampler, batch_size=batch_size)
#
# val_dataset = TensorDataset(val_input_ids, val_attention_masks, val_labels)
# val_sampler = SequentialSampler(val_dataset)
# val_dataloader = DataLoader(val_dataset, sampler=val_sampler, batch_size=batch_size)
#
# # 8. Initialize BERT model
# model = BertForSequenceClassification.from_pretrained(
#     'bert-base-multilingual-cased',
#     num_labels=3,
#     output_attentions=False,
#     output_hidden_states=False
# )
#
# # 9. Set up device and move model to device
# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# model.to(device)
#
# # 10. Set up optimizer and scheduler
# optimizer = AdamW(model.parameters(), lr=2e-5, eps=1e-8)
# epochs = 4
# total_steps = len(train_dataloader) * epochs
# scheduler = get_linear_schedule_with_warmup(
#     optimizer,
#     num_warmup_steps=0,
#     num_training_steps=total_steps
# )
#
#
# # 11. Training loop with progress tracking
# def train_model():
#     for epoch in range(epochs):
#         print(f'\nEpoch {epoch + 1}/{epochs}')
#         print('-' * 10)
#
#         # Training
#         model.train()
#         total_train_loss = 0
#         train_correct = 0
#         train_total = 0
#
#         for batch in tqdm(train_dataloader, desc='Training'):
#             batch_input_ids = batch[0].to(device)
#             batch_attention_mask = batch[1].to(device)
#             batch_labels = batch[2].to(device)
#
#             model.zero_grad()
#
#             outputs = model(
#                 batch_input_ids,
#                 attention_mask=batch_attention_mask,
#                 labels=batch_labels
#             )
#
#             loss = outputs.loss
#             total_train_loss += loss.item()
#
#             # Calculate training accuracy
#             logits = outputs.logits
#             preds = torch.argmax(logits, dim=1)
#             train_correct += (preds == batch_labels).sum().item()
#             train_total += len(batch_labels)
#
#             loss.backward()
#             torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
#             optimizer.step()
#             scheduler.step()
#
#         avg_train_loss = total_train_loss / len(train_dataloader)
#         train_accuracy = train_correct / train_total
#         print(f'Training Loss: {avg_train_loss:.4f}')
#         print(f'Training Accuracy: {train_accuracy:.4f}')
#
#         # Validation
#         model.eval()
#         total_val_loss = 0
#         val_correct = 0
#         val_total = 0
#         val_preds = []
#         val_true = []
#
#         for batch in tqdm(val_dataloader, desc='Validation'):
#             batch_input_ids = batch[0].to(device)
#             batch_attention_mask = batch[1].to(device)
#             batch_labels = batch[2].to(device)
#
#             with torch.no_grad():
#                 outputs = model(
#                     batch_input_ids,
#                     attention_mask=batch_attention_mask,
#                     labels=batch_labels
#                 )
#
#             loss = outputs.loss
#             total_val_loss += loss.item()
#
#             logits = outputs.logits
#             preds = torch.argmax(logits, dim=1)
#             val_correct += (preds == batch_labels).sum().item()
#             val_total += len(batch_labels)
#
#             val_preds.extend(preds.cpu().numpy())
#             val_true.extend(batch_labels.cpu().numpy())
#
#         avg_val_loss = total_val_loss / len(val_dataloader)
#         val_accuracy = val_correct / val_total
#         print(f'Validation Loss: {avg_val_loss:.4f}')
#         print(f'Validation Accuracy: {val_accuracy:.4f}')
#
#         # Classification report
#         print('\nClassification Report:')
#         print(classification_report(val_true, val_preds, target_names=sentiment_map.keys()))
#
#
# # 12. Start training
# print("\nStarting training...")
# train_model()
#
# # 13. Save the trained model
# print("\nSaving model...")
# model.save_pretrained('./hate_speech_detector')
# tokenizer.save_pretrained('./hate_speech_detector')
# print("Model saved successfully!")


# ========================================================================


# train_sentiment_mbert.py

print("latest")
# import os
# import re
# import math
# import json
# import random
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
#
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, confusion_matrix
# from sklearn.utils.class_weight import compute_class_weight
#
# import torch
# from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
#
# from transformers import (
#     BertTokenizer, BertForSequenceClassification,
#     get_linear_schedule_with_warmup, DataCollatorWithPadding
# )
# from torch.optim import AdamW
# from tqdm import tqdm
#
# # --------------------
# # Config
# # --------------------
# SEED = 42
# MODEL_NAME = "bert-base-multilingual-cased"  # or try "xlm-roberta-base" for multilingual gains
# MAX_LEN = 128
# BATCH_SIZE = 32
# LR = 2e-5
# EPS = 1e-8
# WEIGHT_DECAY = 0.01
# EPOCHS = 4
# WARMUP_RATIO = 0.1
# OUTPUT_DIR = "./model_checkpoints"
# FINAL_DIR = "./final_model"
# PLOT_DIR = "./plots"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
# os.makedirs(FINAL_DIR, exist_ok=True)
# os.makedirs(PLOT_DIR, exist_ok=True)
#
# random.seed(SEED)
# np.random.seed(SEED)
# torch.manual_seed(SEED)
# torch.cuda.manual_seed_all(SEED)
#
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f"Using device: {device}")
#
# # --------------------
# # Data loading / cleaning
# # --------------------
# # Use the cleaned file I prepared; replace with your own path if needed.
# DATA_PATH = "D:\\RISS 2025-26\\Cyber_Safe_Social_media\\Cyber_safe_Project\\Cyber_Safe_Social_Media\\sentiment_dataset.csv"  # or your absolute path
#
# def load_csv_robust(path):
#     # try utf-8 first, else fallback
#     try:
#         return pd.read_csv(path, encoding="utf-8")
#     except Exception:
#         for enc in ["latin1", "ISO-8859-1", "cp1252"]:
#             try:
#                 return pd.read_csv(path, encoding=enc)
#             except Exception:
#                 continue
#         raise RuntimeError("Failed to read CSV with common encodings.")
#
# def basic_clean(s: str) -> str:
#     if not isinstance(s, str):
#         return ""
#     s = s.strip()
#     s = re.sub(r"\s+", " ", s)
#     return s
#
# df = load_csv_robust(DATA_PATH)
#
# # Keep only expected columns/labels
# assert {"text", "sentiment"}.issubset(df.columns), "CSV must have 'text' and 'sentiment' columns."
# df["text"] = df["text"].apply(basic_clean)
# df = df.dropna(subset=["text"])
# df["sentiment"] = df["sentiment"].str.strip().str.lower()
#
# valid_labels = {"positive", "negative", "neutral"}
# df = df[df["sentiment"].isin(valid_labels)].reset_index(drop=True)
#
# # Label map
# label2id = {"positive": 0, "neutral": 1, "negative": 2}
# id2label = {v: k for k, v in label2id.items()}
# df["label"] = df["sentiment"].map(label2id)
#
# print("\nClass distribution:")
# print(df["sentiment"].value_counts())
#
# # Plot class distribution
# plt.figure(figsize=(6,4))
# df["sentiment"].value_counts().plot(kind="bar")
# plt.title("Class Distribution")
# plt.xlabel("Sentiment")
# plt.ylabel("Count")
# plt.tight_layout()
# plt.savefig(os.path.join(PLOT_DIR, "class_distribution.png"))
# plt.close()
#
# # --------------------
# # Split
# # --------------------
# train_texts, temp_texts, train_labels, temp_labels = train_test_split(
#     df["text"].astype(str),
#     df["label"].astype(int),
#     test_size=0.30,
#     random_state=SEED,
#     stratify=df["label"].astype(int)
# )
#
# val_texts, test_texts, val_labels, test_labels = train_test_split(
#     temp_texts,
#     temp_labels,
#     test_size=0.50,
#     random_state=SEED,
#     stratify=temp_labels
# )
#
# print(f"\nSplit sizes -> train: {len(train_texts)}, val: {len(val_texts)}, test: {len(test_texts)}")
#
# # --------------------
# # Tokenizer & Encoding
# # --------------------
# tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
#
# def encode_texts(texts, desc):
#     input_ids, attention_masks = [], []
#     for t in tqdm(texts, desc=desc):
#         t = (t or "").strip()
#         enc = tokenizer.encode_plus(
#             t if t else "[EMPTY]",
#             add_special_tokens=True,
#             max_length=MAX_LEN,
#             padding="max_length",
#             truncation=True,
#             return_attention_mask=True,
#             return_tensors="pt",
#         )
#         input_ids.append(enc["input_ids"])
#         attention_masks.append(enc["attention_mask"])
#     return torch.cat(input_ids, dim=0), torch.cat(attention_masks, dim=0)
#
# print("\nTokenizing...")
# train_input_ids, train_attention_masks = encode_texts(train_texts, "Encode train")
# val_input_ids, val_attention_masks = encode_texts(val_texts, "Encode val")
# test_input_ids, test_attention_masks = encode_texts(test_texts, "Encode test")
#
# train_labels_t = torch.tensor(train_labels.values)
# val_labels_t   = torch.tensor(val_labels.values)
# test_labels_t  = torch.tensor(test_labels.values)
#
# # --------------------
# # DataLoaders
# # --------------------
# train_dataset = TensorDataset(train_input_ids, train_attention_masks, train_labels_t)
# val_dataset   = TensorDataset(val_input_ids, val_attention_masks, val_labels_t)
# test_dataset  = TensorDataset(test_input_ids, test_attention_masks, test_labels_t)
#
# train_loader = DataLoader(train_dataset, sampler=RandomSampler(train_dataset), batch_size=BATCH_SIZE)
# val_loader   = DataLoader(val_dataset, sampler=SequentialSampler(val_dataset), batch_size=BATCH_SIZE)
# test_loader  = DataLoader(test_dataset, sampler=SequentialSampler(test_dataset), batch_size=BATCH_SIZE)
#
# # --------------------
# # Model
# # --------------------
# model = BertForSequenceClassification.from_pretrained(
#     MODEL_NAME,
#     num_labels=3,
#     id2label=id2label,
#     label2id=label2id,
#     output_attentions=False,
#     output_hidden_states=False
# ).to(device)
#
# # Class weights (optional, helpful if imbalanced)
# classes = np.array([0,1,2])
# class_weights = compute_class_weight(
#     class_weight="balanced",
#     classes=classes,
#     y=train_labels.values
# )
# class_weights_t = torch.tensor(class_weights, dtype=torch.float, device=device)
# print(f"\nClass weights: {class_weights}")
#
# # Optimizer & scheduler
# optimizer = AdamW(model.parameters(), lr=LR, eps=EPS, weight_decay=WEIGHT_DECAY)
# total_steps = len(train_loader) * EPOCHS
# warmup_steps = int(WARMUP_RATIO * total_steps)
# scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)
#
# # --------------------
# # Train/Eval helpers
# # --------------------
# def evaluate(dataloader):
#     model.eval()
#     total_loss = 0.0
#     preds_all, labels_all = [], []
#     with torch.no_grad():
#         for batch in tqdm(dataloader, desc="Eval"):
#             b_input_ids = batch[0].to(device)
#             b_masks     = batch[1].to(device)
#             b_labels    = batch[2].to(device)
#
#             outputs = model(
#                 b_input_ids,
#                 attention_mask=b_masks,
#                 labels=b_labels
#             )
#             loss = outputs.loss
#             logits = outputs.logits
#
#             total_loss += loss.item()
#             preds = torch.argmax(logits, dim=1)
#             preds_all.extend(preds.detach().cpu().numpy())
#             labels_all.extend(b_labels.detach().cpu().numpy())
#     avg_loss = total_loss / max(1, len(dataloader))
#     return avg_loss, np.array(labels_all), np.array(preds_all)
#
# def train():
#     best_val_acc = -1.0
#     history = []
#     for epoch in range(EPOCHS):
#         print(f"\nEpoch {epoch+1}/{EPOCHS}")
#         model.train()
#         total_train_loss = 0.0
#         correct, total = 0, 0
#
#         for batch in tqdm(train_loader, desc="Train"):
#             b_input_ids = batch[0].to(device)
#             b_masks     = batch[1].to(device)
#             b_labels    = batch[2].to(device)
#
#             model.zero_grad()
#
#             outputs = model(
#                 b_input_ids,
#                 attention_mask=b_masks,
#                 labels=b_labels
#             )
#             # Apply class weighting to loss if available
#             logits = outputs.logits
#             # Replace default loss with weighted CE
#             loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights_t)
#             loss = loss_fn(logits, b_labels)
#
#             total_train_loss += loss.item()
#
#             preds = torch.argmax(logits, dim=1)
#             correct += (preds == b_labels).sum().item()
#             total += b_labels.size(0)
#
#             loss.backward()
#             torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
#             optimizer.step()
#             scheduler.step()
#
#         train_loss = total_train_loss / max(1, len(train_loader))
#         train_acc = correct / max(1, total)
#
#         val_loss, y_true, y_pred = evaluate(val_loader)
#         val_acc = (y_true == y_pred).mean()
#
#         # Save best
#         if val_acc > best_val_acc:
#             best_val_acc = val_acc
#             torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, "best_model.pt"))
#             print(f"Saved new best model (val_acc={val_acc:.4f})")
#
#         history.append({
#             "epoch": epoch+1,
#             "train_loss": train_loss,
#             "train_acc": train_acc,
#             "val_loss": val_loss,
#             "val_acc": val_acc
#         })
#
#         print(f"Train Loss {train_loss:.4f} | Train Acc {train_acc:.4f} | Val Loss {val_loss:.4f} | Val Acc {val_acc:.4f}")
#
#         # Per-epoch report & confusion matrix
#         print("\nValidation classification report:")
#         print(classification_report(y_true, y_pred, target_names=["positive","neutral","negative"]))
#
#         cm = confusion_matrix(y_true, y_pred, labels=[0,1,2])
#         plt.figure(figsize=(6,5))
#         plt.imshow(cm, interpolation='nearest')
#         plt.title(f'Confusion Matrix - Epoch {epoch+1}')
#         plt.xlabel('Predicted')
#         plt.ylabel('Actual')
#         plt.xticks([0,1,2], ["positive","neutral","negative"])
#         plt.yticks([0,1,2], ["positive","neutral","negative"])
#         for (i,j), v in np.ndenumerate(cm):
#             plt.text(j, i, str(v), ha='center', va='center')
#         plt.tight_layout()
#         plt.savefig(os.path.join(PLOT_DIR, f"confusion_epoch_{epoch+1}.png"))
#         plt.close()
#
#     # Save final model and history
#     torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, "final_model.pt"))
#     with open(os.path.join(OUTPUT_DIR, "history.json"), "w") as f:
#         json.dump(history, f, indent=2)
#     return history
#
# print("\nStarting training...")
# history = train()
#
# # Training curves
# hist_df = pd.DataFrame(history).set_index("epoch")
# plt.figure(figsize=(10,4))
# plt.plot(hist_df["train_loss"], label="train_loss")
# plt.plot(hist_df["val_loss"], label="val_loss")
# plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.title("Loss Curves"); plt.legend()
# plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, "loss_curves.png")); plt.close()
#
# plt.figure(figsize=(10,4))
# plt.plot(hist_df["train_acc"], label="train_acc")
# plt.plot(hist_df["val_acc"], label="val_acc")
# plt.xlabel("Epoch"); plt.ylabel("Accuracy"); plt.title("Accuracy Curves"); plt.legend()
# plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, "acc_curves.png")); plt.close()
#
# # --------------------
# # Test evaluation
# # --------------------
# print("\nEvaluating on test set...")
# model.load_state_dict(torch.load(os.path.join(OUTPUT_DIR, "best_model.pt"), map_location=device))
# model.eval()
#
# all_preds, all_true = [], []
# with torch.no_grad():
#     for batch in tqdm(test_loader, desc="Test"):
#         b_input_ids = batch[0].to(device)
#         b_masks     = batch[1].to(device)
#         b_labels    = batch[2].to(device)
#         outputs = model(b_input_ids, attention_mask=b_masks)
#         preds = torch.argmax(outputs.logits, dim=1)
#         all_preds.extend(preds.detach().cpu().numpy())
#         all_true.extend(b_labels.detach().cpu().numpy())
#
# all_preds = np.array(all_preds)
# all_true = np.array(all_true)
# test_acc = (all_true == all_preds).mean()
# print(f"\nTest Accuracy: {test_acc:.4f}")
# print("\nTest classification report:")
# print(classification_report(all_true, all_preds, target_names=["positive","neutral","negative"]))
#
# cm = confusion_matrix(all_true, all_preds, labels=[0,1,2])
# plt.figure(figsize=(6,5))
# plt.imshow(cm, interpolation='nearest')
# plt.title('Test Confusion Matrix')
# plt.xlabel('Predicted')
# plt.ylabel('Actual')
# plt.xticks([0,1,2], ["positive","neutral","negative"])
# plt.yticks([0,1,2], ["positive","neutral","negative"])
# for (i,j), v in np.ndenumerate(cm):
#     plt.text(j, i, str(v), ha='center', va='center')
# plt.tight_layout()
# plt.savefig(os.path.join(PLOT_DIR, "confusion_test.png"))
# plt.close()
#
# # --------------------
# # Save final model/tokenizer for inference
# # --------------------
# model.save_pretrained(FINAL_DIR)
# tokenizer.save_pretrained(FINAL_DIR)
# print("\nSaved model & tokenizer to:", FINAL_DIR)
#
# # --------------------
# # Quick inference helper (example)
# # --------------------
# def predict_sentiment(texts):
#     model.eval()
#     results = []
#     for t in texts:
#         enc = tokenizer(
#             t, truncation=True, padding="max_length", max_length=MAX_LEN, return_tensors="pt"
#         )
#         enc = {k: v.to(device) for k, v in enc.items()}
#         with torch.no_grad():
#             out = model(**enc)
#             pred = torch.argmax(out.logits, dim=1).item()
#             results.append(id2label[pred])
#     return results

# Example:
# print(predict_sentiment(["I love this!", "I hate it.", "Okayish."]))

#
import pandas as pd
import torch
import os
import warnings
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from transformers import (
    BertTokenizer, BertForSequenceClassification,
    pipeline, get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from tqdm import tqdm

# Suppress warnings
warnings.filterwarnings('ignore')

# ================== CONSTANTS ==================
MODEL_DIR = "final_model"  # Directory to save/load Manglish model
DATASET_PATH = "sentiment_dataset.csv"  # Dataset path
MAX_LENGTH = 128
BATCH_SIZE = 32
EPOCHS = 3
LEARNING_RATE = 2e-5
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
TRAIN_MODEL = False  # Toggle: True to retrain Manglish model

# ================== DATA PREPARATION ==================
def load_and_clean_data(filepath):
    print(f"📂 Loading dataset from {filepath}")
    df = pd.read_csv(filepath)
    df = df.dropna(subset=['text'])
    df['sentiment'] = df['sentiment'].fillna('neutral')
    print(f"📊 Final dataset size: {len(df)} rows")
    return df

# ================== TRAIN MANGLESH MODEL ==================
def train_manglish_model():
    print("🛠️ Training Manglish model...")
    df = load_and_clean_data(DATASET_PATH)

    sentiment_map = {'positive': 0, 'neutral': 1, 'negative': 2}
    df['label'] = df['sentiment'].map(sentiment_map)

    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['text'].astype(str), df['label'],
        test_size=0.2, random_state=42, stratify=df['label']
    )

    tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

    def encode_texts(texts):
        return tokenizer(
            list(texts),
            padding='max_length',
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors='pt'
        )

    train_encodings = encode_texts(train_texts)
    val_encodings = encode_texts(val_texts)

    train_dataset = TensorDataset(
        train_encodings['input_ids'],
        train_encodings['attention_mask'],
        torch.tensor(train_labels.values)
    )
    val_dataset = TensorDataset(
        val_encodings['input_ids'],
        val_encodings['attention_mask'],
        torch.tensor(val_labels.values)
    )

    train_loader = DataLoader(train_dataset, sampler=RandomSampler(train_dataset), batch_size=BATCH_SIZE)
    val_loader = DataLoader(val_dataset, sampler=SequentialSampler(val_dataset), batch_size=BATCH_SIZE)

    model = BertForSequenceClassification.from_pretrained(
        'bert-base-multilingual-cased', num_labels=3
    ).to(DEVICE)

    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=len(train_loader) * EPOCHS)

    for epoch in range(EPOCHS):
        print(f"\n🔥 Epoch {epoch+1}/{EPOCHS}")
        model.train()
        total_loss, correct, total = 0, 0, 0

        for batch in tqdm(train_loader, desc="Training"):
            b_input_ids, b_masks, b_labels = [t.to(DEVICE) for t in batch]
            model.zero_grad()
            outputs = model(b_input_ids, attention_mask=b_masks, labels=b_labels)
            loss, logits = outputs.loss, outputs.logits
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            preds = torch.argmax(logits, dim=1)
            correct += (preds == b_labels).sum().item()
            total += len(b_labels)

        print(f"📊 Train Loss: {total_loss/len(train_loader):.4f}, Acc: {correct/total:.4f}")

        # Validation
        model.eval()
        val_preds, val_true = [], []
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validating"):
                b_input_ids, b_masks, b_labels = [t.to(DEVICE) for t in batch]
                outputs = model(b_input_ids, attention_mask=b_masks, labels=b_labels)
                preds = torch.argmax(outputs.logits, dim=1)
                val_preds.extend(preds.cpu().numpy())
                val_true.extend(b_labels.cpu().numpy())

        print("\n📝 Validation Report:")
        print(classification_report(val_true, val_preds, target_names=sentiment_map.keys(), digits=4))

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print(f"✅ Model saved at {MODEL_DIR}")

# ================== ENGLISH DETECTOR ==================
def setup_english_detector():
    print("🔤 Loading English model...")
    return pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

# ================== TOXICITY DETECTOR ==================
class ToxicityDetector:
    def __init__(self):
        if not os.path.exists(MODEL_DIR):
            raise FileNotFoundError("Manglish model not found. Please train first.")
        self.manglish_tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
        self.manglish_model = BertForSequenceClassification.from_pretrained(MODEL_DIR).to(DEVICE)
        self.manglish_model.eval()
        self.english_detector = setup_english_detector()
        self.english_threshold = 0.7
        print("🚀 Detector Ready!")

    def is_english(self, text):
        words = text.split()
        return (sum(w.isalpha() for w in words) / len(words)) > self.english_threshold if words else False

    def predict_manglish(self, text):
        inputs = self.manglish_tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_LENGTH).to(DEVICE)
        with torch.no_grad():
            outputs = self.manglish_model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        pred = torch.argmax(probs).item()
        return pred, probs[0][pred].item()

    def detect_toxicity(self, text):
        if not text.strip():
            return "neutral", 0.0, "unknown"
        if self.is_english(text):
            result = self.english_detector(text)[0]
            label = "negative" if result['label'] == 'NEGATIVE' else "positive"
            return label, result['score'], "english"
        else:
            pred, conf = self.predict_manglish(text)
            sentiment_map = {0: "positive", 1: "neutral", 2: "negative"}
            return sentiment_map[pred], conf, "manglish"

# ================== MAIN ==================
if __name__ == "__main__":
    print("\n🚀 Multilingual Toxicity Detection System 🚀\n")

    if TRAIN_MODEL:
        train_manglish_model()

    detector = ToxicityDetector()

    while True:
        comment = input("💬 Enter text (or 'exit'): ").strip()
        if comment.lower() == 'exit':
            print("👋 Goodbye!")
            break
        label, conf, lang = detector.detect_toxicity(comment)

        # Colored output
        if label == "negative":
            color = "\033[91m"  # Red
        elif label == "positive":
            color = "\033[92m"  # Green
        else:
            color = "\033[93m"  # Yellow

        print(f"\n🔍 Text: {comment[:100]}{'...' if len(comment)>100 else ''}")
        print(f"🌐 Language: {lang}")
        print(f"📊 Sentiment: {color}{label}\033[0m")
        print(f"🎯 Confidence: {conf:.2%}")
        print(f"⚠️ Toxicity: {color}{'Toxic' if label=='negative' else 'Non-Toxic'}\033[0m")
        print("-"*40)
