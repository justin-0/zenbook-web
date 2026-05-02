import pandas as pd

# Load the dataset with Windows-1252 encoding
df = pd.read_csv('D:\\RISS 2025-26\\Cyber_Safe_Social_media\\Cyber_safe_Project\\Cyber_Safe_Social_Media\\sentiment_dataset.csv',
                 encoding='windows-1252')

# Keep only Manglish rows
df_manglish = df[df['language'] == 'Manglish']

# Save the filtered dataset
df_manglish.to_csv('manglish_sentiment_dataset.csv', index=False, encoding='utf-8')

print(f"Filtered dataset saved. Original rows: {len(df)}, Manglish rows: {len(df_manglish)}")