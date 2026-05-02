



from transformers import pipeline, BertTokenizer, BertForSequenceClassification
import torch
from langdetect import detect, LangDetectException
import re
import os
import warnings

class ToxicityAnalyzer:
    """A class for analyzing toxicity in both English and Manglish text"""

    def __init__(self):
        warnings.filterwarnings('ignore')
        self.obvious_toxic_english = {
            'fuck', 'shit', 'asshole', 'bitch', 'damn', 'crap', 'hell',
            'dick', 'piss', 'bastard', 'douche', 'cunt', 'whore', 'slut',
            'faggot', 'idiot', 'moron', 'retard', 'jerk', 'twat', 'bloody'
        }
        self.obvious_manglish = {
            'pottan','mandan', 'myre', 'thayoli', 'koothichi', 'thevidichi', 'kundi',
            'poori mone', 'kunnan', 'funda', 'fundachi', 'kunna', 'koora',
            'kachi', 'poondachi', 'pari', 'chodi', 'koothi',
            'polayadi', 'patti', 'thendi', 'poore', 'chodu', 'nayinte mone',
            'chettah', 'chutti', 'paapam', 'thotti', 'pandi karimbara', 'koothi mone',
            'oomba', 'andi', 'oomb', 'oomban', 'vaanam', 'koothara', 'vettu',
            'kandu', 'oombada ', 'patti','kazhuveri ','kalinte edele',
        }
        self.common_neutral_english = {
            'hi', 'hello', 'hey', 'ok', 'okay', 'yes', 'no', 'thanks', 'please',
            'poyalo', 'achan', 'vaa', 'macha', 'nee','poda','chettan','para','vas','dude','podi'
        }
        self.english_toxicity_model = None
        self.manglish_tokenizer = None
        self.manglish_model = None
        self.device = None

        self.initialize_models()

    def initialize_models(self):
        """Load models"""
        print("\n🚀 Initializing Combined Toxicity Analyzer...")

        # English toxicity model
        print("Loading English toxicity model...")
        self.english_toxicity_model = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

        # Manglish model
        print("Loading Manglish sentiment model...")
        try:
            base_dir = os.path.dirname(__file__)
            manglish_model_path = os.path.join(base_dir, "manglish_sentiment_model")

            self.manglish_tokenizer = BertTokenizer.from_pretrained(manglish_model_path)
            self.manglish_model = BertForSequenceClassification.from_pretrained(manglish_model_path)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.manglish_model = self.manglish_model.to(self.device)

            print("✅ Models loaded successfully!")
            print(f"🖥️  Using device: {self.device}")

        except Exception as e:
            print(f"⚠️ Failed to load Manglish model: {e}")
            self.manglish_model = None

    def detect_language(self, text):
        """Detect language"""
        text_lower = text.lower().strip()

        if any(re.search(rf"\b{re.escape(word)}\b", text_lower) for word in self.obvious_toxic_english):
            return "english"

        if any(re.search(rf"\b{re.escape(word)}\b", text_lower) for word in self.obvious_manglish):
            return "manglish"

        try:
            lang = detect(text)
            return "english" if lang == "en" else "manglish"
        except LangDetectException:
            return "english"

    def is_gibberish(self, text):
        """Detect gibberish/random strings (force Non-Toxic)"""
        words = text.split()
        # if words are very short, not in dictionary, or mostly consonants
        gibberish_count = sum(
            1 for w in words if not re.match(r"^[a-zA-Z]+$", w) or len(set(w)) < 3
        )
        return gibberish_count == len(words)  # all words look fake

    def check_toxic_words(self, text):
        """Detect toxic words in the text"""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        toxic_english_found = [word for word in words if word in self.obvious_toxic_english]
        toxic_manglish_found = [word for word in words if word in self.obvious_manglish]
        neutral_found = [word for word in words if word in self.common_neutral_english]

        if toxic_english_found or toxic_manglish_found:
            return "Toxic", toxic_english_found, toxic_manglish_found, neutral_found

        if neutral_found and all(word in self.common_neutral_english for word in words):
            return "Neutral", [], [], neutral_found

        return None, [], [], neutral_found

    def analyze_toxicity(self, text):
        """Analyze toxicity"""
        if not text.strip():
            return {"error": "Empty text input"}, 0.0, "unknown", [], [], []

        # Step 0: Check gibberish
        if self.is_gibberish(text):
            return "Non-Toxic", 0.0, "unknown", [], [], []

        # Step 1: Detect any obvious toxic words first
        immediate_result, toxic_english, toxic_manglish, neutral_words = self.check_toxic_words(text)
        if immediate_result:
            language = self.detect_language(text)
            confidence = 0.95
            return immediate_result, confidence, language, toxic_english, toxic_manglish, neutral_words

        # Step 2: Use model for language-specific analysis
        language = self.detect_language(text)

        if language == "english":
            result = self.english_toxicity_model(text)[0]
            label = result["label"]
            score = result["score"]

            # only classify toxic if high confidence
            if label == "NEGATIVE" and score > 0.7:
                toxicity = "Toxic"
            else:
                toxicity = "Non-Toxic"

            return toxicity, score, language, [], [], []

        elif language == "manglish" and self.manglish_model:
            inputs = self.manglish_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding="max_length"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.manglish_model(**inputs)

            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            pred = torch.argmax(probs).item()
            confidence = probs[0][pred].item()

            # Add confidence threshold
            if confidence < 0.7:
                return "Non-Toxic", confidence, language, [], [], []

            if pred == 2:
                toxicity = "Toxic"
            elif pred == 1:
                toxicity = "Non-Toxic"
            else:
                toxicity = "Neutral"

            return toxicity, confidence, language, [], [], []

        return "Non-Toxic", 0.0, language, [], [], []

    def display_result(self, text, result, confidence, language, toxic_english, toxic_manglish, neutral_words):
        """Display results"""
        if isinstance(result, dict):
            print(f"\n❌ Error: {result['error']}")
            return

        print("\n" + "=" * 60)
        print(f"📝 Text: {text}")
        print(f"🌐 Language: {language.upper()}")
        print(f"⚠️  Toxicity: {result}")
        print(f"📊 Confidence: {confidence:.1%}")

        if toxic_english:
            print(f"🔴 Toxic English words detected: {', '.join(toxic_english)}")
        if toxic_manglish:
            print(f"🔴 Toxic Manglish words detected: {', '.join(toxic_manglish)}")
        if neutral_words:
            print(f"🟢 Neutral words detected: {', '.join(neutral_words)}")
        print("=" * 60)

    def run_interactive(self):
        """Run in interactive mode"""
        print("\n🔍 Combined English/Manglish Toxicity Detection System")
        print("====================================================")
        print("Type 'exit' to quit\n")

        try:
            while True:
                text = input("💬 Enter text: ").strip()
                if text.lower() in ('exit', 'quit'):
                    print("\n👋 Goodbye!")
                    break

                toxicity, confidence, language, toxic_english, toxic_manglish, neutral_words = self.analyze_toxicity(text)
                self.display_result(text, toxicity, confidence, language, toxic_english, toxic_manglish, neutral_words)

        except Exception as e:
            print(f"\n❌ Failed to run analyzer: {str(e)}")


if __name__ == "__main__":
    analyzer = ToxicityAnalyzer()
    analyzer.run_interactive()
