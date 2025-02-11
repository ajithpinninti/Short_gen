#############################
# audio_processor.py
#############################
import os
import whisper
from moviepy.audio.io.AudioFileClip import AudioFileClip
from utils import time_to_seconds
import re
import pickle
CACHE_FILE = "temp/processed_result_cache.pkl"



def transcribe_with_timestamps(audio_path, train):
    """Convert audio to text with word-level timestamps using Whisper"""
    ####################Cache the processed audio####################
    # Check if cached audio exists
    if os.path.exists(CACHE_FILE) and not train:
        print("Loading cached processed_audio...")
        with open(CACHE_FILE, "rb") as f:
            result = pickle.load(f)
    else:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)

        print("loading speech to text model ....    ")
        model = whisper.load_model("medium", device="cpu")
        print("Processing audio and caching the result...")
        result = model.transcribe(audio_path, fp16=False, word_timestamps=True)

    # Save to cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(result, f)

    ###############################################################   
    return result["segments"]

def align_script_with_audio(script_path, audio_segments):
    """
    Aligns the original script with the audio transcription.
    This function reads a script from a file and aligns it with the provided audio segments.
    It ensures that each word in the script corresponds to a word in the audio segments.
    Args:
        script_path (str): The file path to the script.
        audio_segments (list): A list of dictionaries, where each dictionary represents an audio segment
                               and contains 'words' (a list of word dictionaries with 'word', 'start', and 'end' keys),
                               'text' (the transcribed text of the segment), 'start' (start time of the segment),
                               and 'end' (end time of the segment).
    Returns:
        list: A list of dictionaries, where each dictionary contains:
              - 'script_line' (str): A line from the script.
              - 'words' (list): A list of word dictionaries with 'text', 'start', and 'end' keys.
              - 'start' (float): The start time of the segment.
              - 'end' (float): The end time of the segment.
    Raises:
        ValueError: If the number of words in the audio segments does not match the number of words in the script.
    """
    with open(script_path, encoding="utf-8") as f:
        script_lines = [line.strip() for line in f.readlines()]
    
    # converting audio_segments into list of words ####
    audio_words = []
    for segment in audio_segments:
        audio_words += segment['words']
    ######################################################
    script = {}
    script["script_lines"] = script_lines
    script["script_len"] = len(script_lines)
    script["script_line_words"] = []
    script["script_all_words"] = []
    for text in script_lines:
        # text = re.sub(r'[^a-zA-Z\s]', '', text) #removing all special characters
        script_words = re.findall(r"\b[\w]+(?:'[\w]+)?\b", text)
        script["script_all_words"] += script_words
        script["script_line_words"].append(script_words)
        # todo: change the text in every word object in segment ( later)

    # checking the number of audio_words and script_lines words
    if ( len(audio_words) == len( script['script_all_words']) ):
        #iterate through every segment word and replace with script word
        word_ind = 0
        # audio_segments
        for idx,segment in enumerate(audio_segments):
            if idx >= script['script_len']:
                audio_segments = audio_segments[0:idx]
                break
            
            segment['text'] = script['script_lines'][idx]
            segment['words'] = audio_words[
                word_ind:len(script['script_line_words'][idx]) + word_ind
            ]
            word_ind += len(script['script_line_words'][idx])
            # for seg_word in  script['script_line_words'][idx] :
            #     seg_word = script['script_line_words'][word_ind]
            #     word_ind+=1
            segment['start'] = segment['words'][0]['start']
            segment['end'] = segment['words'][-1]['end']
        
        

    else:
        print("#########Number of words in audio and script are not equal#########3")
        print("Number of words in audio: ", len(audio_words))
        for segment in audio_segments:
            print(segment['text'])
        print("Number of words in script: ", len(script['script_all_words']))
        print(script['script_all_words'])
        return

    aligned_data = []
    for idx, segment in enumerate(audio_segments):
        if idx >= len(script_lines):
            break
        words = []
        for word in segment['words']:
            words.append({
                'text': word['word'],
                'start': word['start'],
                'end': word['end']
            })
        
        aligned_data.append({
            'script_line': script_lines[idx],
            'words': words,
            'start': segment['start'],
            'end': segment['end']
        })
    
    return aligned_data

def process_audio(audio_path, script_path, train):
    """Main audio processing function"""
    print("Processing audio...")
    audio_segments = transcribe_with_timestamps(audio_path, train)
    aligned_data = align_script_with_audio(script_path, audio_segments)
    print("audio process is completed")
    return {
        'raw_audio_path': audio_path,
        'aligned_data': aligned_data
    }
