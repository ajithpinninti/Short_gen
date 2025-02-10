#############################
# audio_processor.py
#############################
import os
import whisper
from difflib import SequenceMatcher
from moviepy.audio.io.AudioFileClip import AudioFileClip
from utils import time_to_seconds
import re
import pickle

CACHE_FILE = "processed_result_cache.pkl"



def transcribe_with_timestamps(audio_path):
    """Convert audio to text with word-level timestamps using Whisper"""
    print("loading speech to text model ....    ")
    #model = whisper.load_model("medium")
    print("speech to text model running ....    ")

    ####################Cache the processed audio####################
    # Check if cached audio exists
    if os.path.exists(CACHE_FILE):
        print("Loading cached processed_audio...")
        with open(CACHE_FILE, "rb") as f:
            result = pickle.load(f)
    else:
        print("Processing audio and caching the result...")
        model = whisper.load_model("medium") #large-v1
        #['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small',
        # 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large',
        #  'large-v3-turbo', 'turbo']
        result = model.transcribe(audio_path, fp16=False, word_timestamps=True)

    # Save to cache
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(result, f)
    ##############################################################   
    print(result['text'])
    return result["segments"]


def align_audio_with_script(script_path, audio_segments):

    with open(script_path, encoding="utf-8") as f:
        script_lines = [line.strip() for line in f.readlines()]

    # Flatten all audio words from segments
    audio_words = []
    for segment in audio_segments:
        audio_words.extend(segment['words'])  # word class object
    
    # Process script lines into words
    script_line_words = []
    script_all_words = []
    for line in script_lines:
        line_processed = line.replace('-', ' ')
        words = re.findall(r"\b\w+(?:'\w+)?\b", line_processed)
        script_line_words.append(words)
        script_all_words.extend(words)
    
    # Check total words match
    if len(audio_words) != len(script_all_words):
        print("Word count mismatch between audio and script.")
        print(f"Audio words: {len(audio_words)}, Script words: {len(script_all_words)}")
        print("Attempting fuzzy alignment...")
    
    # Fuzzy alignment for mismatched words
    aligned_data = []
    audio_word_idx = 0
    for line_idx, line in enumerate(script_lines):
        line_processed = line.replace('-', ' ')
        script_words = re.findall(r"\b\w+(?:'\w+)?\b", line_processed)
        line_audio_words = []
        
        for script_word in script_words:
            if audio_word_idx >= len(audio_words):
                break  # No more audio words to match
            
            # Find the best match for the script word in the remaining audio words
            best_match_idx = audio_word_idx
            best_match_score = SequenceMatcher(
                None, script_word, audio_words[audio_word_idx]['text']
            ).ratio()
            
            # Check the next few words for a better match (optional: limit search window)
            for i in range(audio_word_idx + 1, min(audio_word_idx + 5, len(audio_words))):
                score = SequenceMatcher(
                    None, script_word, audio_words[i]['text']
                ).ratio()

                if score > best_match_score:
                    best_match_idx = i
                    best_match_score = score
            
            # If the best match score is above a threshold, consider it a match
            if best_match_score > 0.6:  # Adjust threshold as needed
                line_audio_words.append(audio_words[best_match_idx])
                audio_word_idx = best_match_idx + 1
            else:
                # No match found, skip this script word
                print(f"No match found for script word: {script_word}")
                # line_audio_words.append({
                #     'word': script_word,
                #     'start': None,
                #     'end': None
                # })
        
        # Extract start and end times for the line
        if line_audio_words:
            start = line_audio_words[0]['start']
            end = line_audio_words[-1]['end']
        else:
            start = None
            end = None
        
        if line_audio_words == 0:
            print("No audio words found in script line:")
            continue

        # Format aligned entry
        aligned_entry = {
            'script_line': line,
            'words': [{
                'text': word['text'],
                'start': word['start'],
                'end': word['end']
            } for word in line_audio_words],
            'start': start,
            'end': end
        }
        aligned_data.append(aligned_entry)
    
    return aligned_data


def process_audio(audio_path, script_path):
    """Main audio processing function"""
    print("Processing audio...")
    audio_segments = transcribe_with_timestamps(audio_path)
    aligned_data = align_audio_with_script(script_path, audio_segments)
    print("audio process is completed")
    return {
        'raw_audio_path': audio_path,
        'aligned_data': aligned_data
    }
