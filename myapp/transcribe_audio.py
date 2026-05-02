#
#
# import speech_recognition as sr
# from pydub import AudioSegment
# import os
#
#
# def voice_to_text():
#     # Initialize the recognizer
#     recognizer = sr.Recognizer()
#
#     # Path to your AAC file
#     aac_file = r"D:\RISS 2025-26\Cyber_Safe_Social_media\Cyber_safe_Project\Cyber_Safe_Social_Media\media\group_chat_audio\audio_message.aac"
#     wav_file = "converted_audio.wav"
#
#     # Convert AAC to WAV
#     print("Converting AAC to WAV...")
#     audio = AudioSegment.from_file(aac_file, format="aac")
#     audio.export(wav_file, format="wav")
#
#     # Use the audio file as source
#     with sr.AudioFile(wav_file) as source:
#         audio_data = recognizer.record(source)  # Read the entire audio file
#
#     try:
#         # Use Google's speech recognition
#         text = recognizer.recognize_google(audio_data)
#         print(f"Text: {text}")
#
#     except sr.UnknownValueError:
#         print("Could not understand the audio")
#     except sr.RequestError as e:
#         print(f"Could not request results from Google Speech Recognition service; {e}")
#     except Exception as e:
#         print(f"Error: {e}")
#
#     # Clean up (optional)
#     if os.path.exists(wav_file):
#         os.remove(wav_file)
#
#
# if __name__ == "__main__":
#     voice_to_text()



import speech_recognition as sr
from pydub import AudioSegment
import os
import google.generativeai as genai


# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyBZgHHafCNQQEj9Yt-i6W6F4KpdGsnqPew")


def translate_with_gemini(text):
    """Translate Malayalam/English/mixed text into English using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Translate the following Malayalam/English mixed text into pure English:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Translation Error] {e}"


def voice_to_text():
    recognizer = sr.Recognizer()

    # Path to your AAC file
    aac_file = r"D:\RISS 2025-26\Cyber_Safe_Social_media\Cyber_safe_Project\Cyber_Safe_Social_Media\media\group_chat_audio\audio_message.aac"
    wav_file = "converted_audio.wav"

    # Convert AAC to WAV
    print("Converting AAC to WAV...")
    audio = AudioSegment.from_file(aac_file, format="aac")
    audio.export(wav_file, format="wav")

    # Use the audio file as source
    with sr.AudioFile(wav_file) as source:
        audio_data = recognizer.record(source)

    try:
        # ✅ Recognize speech (set language hint if needed)
        # "ml-IN" for Malayalam, "en-US" for English
        text = recognizer.recognize_google(audio_data, language="ml-IN")
        print(f"Raw Transcription: {text}")

        # ✅ Translate using Gemini
        english_text = translate_with_gemini(text)
        print(f"Final English: {english_text}")

    except sr.UnknownValueError:
        print("Could not understand the audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        print(f"Error: {e}")

    # Clean up
    if os.path.exists(wav_file):
        os.remove(wav_file)


if __name__ == "__main__":
    voice_to_text()
