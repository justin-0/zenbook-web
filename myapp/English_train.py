
from transformers import pipeline

# Load the pre-trained sentiment analysis model
classifier = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')


# Function to detect toxic comments
def detect_toxic_comment(comment):
    result = classifier(comment)[0]
    label = result['label']
    score = result['score']

    if label == 'NEGATIVE' and score > 0.7:  # Customize threshold if needed
        return "Toxic"
    else:
        return "Non-Toxic"


# Main loop for user input
print("💬 Enter your comment to check for toxicity (type 'exit' to quit):")

while True:
    user_input = input("Enter comment: ")
    if user_input.lower() == "exit":
        print("👋 Exiting.")
        break
    result = detect_toxic_comment(user_input)
    print(f"🧪 Result: {result}")

