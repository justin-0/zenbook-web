import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import get_linear_schedule_with_warmup
from torch.optim import AdamW
import torch
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from tqdm import tqdm
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')


# 1. Load and clean the dataset
def load_and_clean_data(filepath):
    df = pd.read_csv(filepath)

    # Check for and handle NaN values
    print(f"Before cleaning - Total rows: {len(df)}")
    print(f"NaN values in text column: {df['text'].isna().sum()}")

    # Drop rows with NaN values in text column
    df = df.dropna(subset=['text'])

    # Clean sentiment labels
    df['sentiment'] = df['sentiment'].str.lower().str.strip()
    df['sentiment'] = df['sentiment'].replace({'netural': 'neutral'})  # Fix common typo

    # Fill any remaining NaN in sentiment with 'neutral'
    df['sentiment'] = df['sentiment'].fillna('neutral')

    # Remove any rows with invalid sentiment values
    valid_sentiments = ['positive', 'neutral', 'negative']
    df = df[df['sentiment'].isin(valid_sentiments)]

    print(f"After cleaning - Total rows: {len(df)}")
    return df


# Load and clean the data with your specified path
df = load_and_clean_data(
    'D:\\RISS 2025-26\\Cyber_Safe_Social_media\\Cyber_safe_Project\\Cyber_Safe_Social_Media\\manglish_sentiment_dataset.csv')

# 2. Map sentiments to numerical values
sentiment_map = {'positive': 0, 'neutral': 1, 'negative': 2}
df['label'] = df['sentiment'].map(sentiment_map)

# Check class distribution
print("\nClass distribution:")
print(df['sentiment'].value_counts())

# 3. Split data into train and validation sets
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['text'].astype(str),  # Ensure all texts are strings
    df['label'],
    test_size=0.2,
    random_state=42,
    stratify=df['label']
)

# 4. Initialize BERT tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')


# 5. Tokenize and encode the texts with improved error handling
def encode_texts(texts):
    input_ids = []
    attention_masks = []

    for text in texts:
        try:
            encoded = tokenizer.encode_plus(
                str(text),  # Ensure text is string
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_tensors='pt'
            )
            input_ids.append(encoded['input_ids'])
            attention_masks.append(encoded['attention_mask'])
        except Exception as e:
            print(f"Error encoding text: {text}")
            print(f"Error: {e}")
            # Fallback to empty encoding
            empty_encoding = tokenizer.encode_plus(
                "",
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_tensors='pt'
            )
            input_ids.append(empty_encoding['input_ids'])
            attention_masks.append(empty_encoding['attention_mask'])

    return torch.cat(input_ids, dim=0), torch.cat(attention_masks, dim=0)


print("\nEncoding training texts...")
train_input_ids, train_attention_masks = encode_texts(train_texts)
print("Encoding validation texts...")
val_input_ids, val_attention_masks = encode_texts(val_texts)

# 6. Convert labels to tensors
train_labels = torch.tensor(train_labels.values)
val_labels = torch.tensor(val_labels.values)

# 7. Create DataLoader
batch_size = 32

train_dataset = TensorDataset(train_input_ids, train_attention_masks, train_labels)
train_sampler = RandomSampler(train_dataset)
train_dataloader = DataLoader(train_dataset, sampler=train_sampler, batch_size=batch_size)

val_dataset = TensorDataset(val_input_ids, val_attention_masks, val_labels)
val_sampler = SequentialSampler(val_dataset)
val_dataloader = DataLoader(val_dataset, sampler=val_sampler, batch_size=batch_size)

# 8. Initialize BERT model
model = BertForSequenceClassification.from_pretrained(
    'bert-base-multilingual-cased',
    num_labels=3,
    output_attentions=False,
    output_hidden_states=False
)

# 9. Set up device and move model to device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# 10. Set up optimizer and scheduler
optimizer = AdamW(model.parameters(), lr=2e-5, eps=1e-8)
epochs = 4
total_steps = len(train_dataloader) * epochs
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=0,
    num_training_steps=total_steps
)


# 11. Training loop with progress tracking
def train_model():
    for epoch in range(epochs):
        print(f'\nEpoch {epoch + 1}/{epochs}')
        print('-' * 10)

        # Training
        model.train()
        total_train_loss = 0
        train_correct = 0
        train_total = 0

        for batch in tqdm(train_dataloader, desc='Training'):
            batch_input_ids = batch[0].to(device)
            batch_attention_mask = batch[1].to(device)
            batch_labels = batch[2].to(device)

            model.zero_grad()

            outputs = model(
                batch_input_ids,
                attention_mask=batch_attention_mask,
                labels=batch_labels
            )

            loss = outputs.loss
            total_train_loss += loss.item()

            # Calculate training accuracy
            logits = outputs.logits
            preds = torch.argmax(logits, dim=1)
            train_correct += (preds == batch_labels).sum().item()
            train_total += len(batch_labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

        avg_train_loss = total_train_loss / len(train_dataloader)
        train_accuracy = train_correct / train_total
        print(f'Training Loss: {avg_train_loss:.4f}')
        print(f'Training Accuracy: {train_accuracy:.4f}')

        # Validation
        model.eval()
        total_val_loss = 0
        val_correct = 0
        val_total = 0
        val_preds = []
        val_true = []

        for batch in tqdm(val_dataloader, desc='Validation'):
            batch_input_ids = batch[0].to(device)
            batch_attention_mask = batch[1].to(device)
            batch_labels = batch[2].to(device)

            with torch.no_grad():
                outputs = model(
                    batch_input_ids,
                    attention_mask=batch_attention_mask,
                    labels=batch_labels
                )

            loss = outputs.loss
            total_val_loss += loss.item()

            logits = outputs.logits
            preds = torch.argmax(logits, dim=1)
            val_correct += (preds == batch_labels).sum().item()
            val_total += len(batch_labels)

            val_preds.extend(preds.cpu().numpy())
            val_true.extend(batch_labels.cpu().numpy())

        avg_val_loss = total_val_loss / len(val_dataloader)
        val_accuracy = val_correct / val_total
        print(f'Validation Loss: {avg_val_loss:.4f}')
        print(f'Validation Accuracy: {val_accuracy:.4f}')

        # Classification report
        print('\nClassification Report:')
        print(classification_report(val_true, val_preds, target_names=sentiment_map.keys()))


# 12. Start training
print("\nStarting training...")
train_model()

# 13. Save the trained model
print("\nSaving model...")
model.save_pretrained('./manglish_sentiment_model')
tokenizer.save_pretrained('./manglish_sentiment_model')
print("Model saved successfully!")


from transformers import BertTokenizer, BertForSequenceClassification
import torch
# import warnings
# import os
# from langdetect import detect
#
# # Suppress warnings
# warnings.filterwarnings('ignore')
#
#
# class ManglishSentimentAnalyzer:
#     def __init__(self, model_path="manglish_sentiment_model"):
#         """Initialize the sentiment analyzer with trained model"""
#         print("\n🚀 Loading Manglish Sentiment Analysis Model...")
#
#         # Verify model exists
#         if not os.path.exists(model_path):
#             raise FileNotFoundError(
#                 f"❌ Model directory '{model_path}' not found. "
#                 "Please train the model first or check the path.")
#
#         # Load model and tokenizer
#         self.tokenizer = BertTokenizer.from_pretrained(model_path)
#         self.model = BertForSequenceClassification.from_pretrained(model_path)
#
#         # Set up device
#         self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#         self.model = self.model.to(self.device)
#
#         # Sentiment mapping
#         self.sentiment_map = {
#             0: {'label': 'positive', 'emoji': '😊', 'color': 'green'},
#             1: {'label': 'neutral', 'emoji': '😐', 'color': 'yellow'},
#             2: {'label': 'negative', 'emoji': '😠', 'color': 'red'}
#         }
#
#         print(f"✅ Model loaded from '{model_path}' successfully!")
#         print(f"🖥️  Using device: {self.device}")
#
#     def detect_language(self, text):
#         """Detect language of the input text"""
#         try:
#             lang = detect(text)
#             return "english" if lang == "en" else "manglish"
#         except:
#             return "unknown"
#
#     def analyze_sentiment(self, text):
#         """Analyze sentiment of input text"""
#         try:
#             if not text.strip():
#                 return {'error': 'Empty text input'}, 0.0, "unknown"
#
#             # Detect language first
#             language = self.detect_language(text)
#
#
#             # Tokenize and encode the text
#             inputs = self.tokenizer(
#                 text,
#                 return_tensors="pt",
#                 truncation=True,
#                 max_length=128,
#                 padding="max_length"
#             ).to(self.device)
#
#             # Make prediction
#             with torch.no_grad():
#                 outputs = self.model(**inputs)
#
#             # Get probabilities and prediction
#             probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
#             pred = torch.argmax(probs).item()
#             confidence = probs[0][pred].item()
#
#             return self.sentiment_map[pred], confidence, language
#
#         except Exception as e:
#             return {'error': str(e)}, 0.0, "unknown"
#
#
# def display_result(text, result, confidence, language):
#     """Display analysis results with formatting"""
#     # Error handling
#     if 'error' in result:
#         print(f"\n⚠️ Error: {result['error']}")
#         return
#
#     # Prepare display elements
#     sentiment = result['label'].upper()
#     emoji = result['emoji']
#     conf_percent = f"{confidence:.1%}"
#     toxicity = "TOXIC 🚨" if result['label'] == 'negative' else 'Non-toxic ✅'
#
#     # Truncate long text for display
#     display_text = text[:100] + ('...' if len(text) > 100 else '')
#
#     # Display results
#     print("\n" + "=" * 60)
#     print(f"📝 Text: {display_text}")
#     print(f"🌐 Language: {language.upper()}")
#     print(f"🎭 Sentiment: {sentiment} {emoji}")
#     print(f"📊 Confidence: {conf_percent}")
#     print(f"⚠️  Toxicity: {toxicity}")
#     print("=" * 60)
#
#
# def main():
#     """Main interactive terminal interface"""
#     print("\n🔍 MANGALOREAN SENTIMENT ANALYZER TERMINAL")
#     print("========================================")
#     print("Type 'exit' or press Ctrl+C to quit\n")
#
#     try:
#         # Initialize analyzer
#         analyzer = ManglishSentimentAnalyzer()
#
#         while True:
#             try:
#                 # Get user input
#                 text = input("💬 Enter text: ")
#
#                 # Exit condition
#                 if text.lower() in ('exit', 'quit'):
#                     print("\n👋 Goodbye! Have a nice day!")
#                     break
#
#                 # Analyze sentiment
#                 result, confidence, language = analyzer.analyze_sentiment(text)
#
#                 # Display results
#                 display_result(text, result, confidence, language)
#
#             except KeyboardInterrupt:
#                 print("\n👋 Session ended by user")
#                 break
#             except Exception as e:
#                 print(f"\n⚠️ Unexpected error: {e}")
#
#     except FileNotFoundError as e:
#         print(e)
#     except Exception as e:
#         print(f"\n❌ Fatal error during initialization: {e}")
#
#
# if __name__ == "__main__":
#     main()