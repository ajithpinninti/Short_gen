#############################
# utils.py
#############################
import os
from moviepy.audio.io.AudioFileClip import AudioFileClip

import os

def validate_inputs(input_dir):
    """Validate input files existence and format"""
    image_dir = os.path.join(input_dir, "images/")
    script_path = os.path.join(input_dir, "script/script.txt")
    audio_dir = os.path.join(input_dir, "audio")  # Set as a directory
    allowed_audio_formats = {".mp3", ".wav", ".ogg"}  # Allowed extensions

    # Validate if the "images" directory exists
    if not os.path.isdir(image_dir):
        print("Image directory not found")
        return False
    if not os.path.isfile(script_path):
        print("Script file not found")
        return False
    
    # Validate if the "audio" directory exists and contains at least one allowed audio file
    if not os.path.isdir(audio_dir):
        print("Audio directory not found")
        return None
    
    audio_dir_file = None
    for f in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, f)
        if os.path.isfile(file_path) and os.path.splitext(f)[1].lower() in allowed_audio_formats:
            audio_dir_file = file_path # Return the first found valid audio file
    
    if audio_dir_file is None:
        print("No valid audio file found in the audio directory")
        return None

    
    return [image_dir, audio_dir_file, script_path]

def check_audio_duration(audio_path):
    """Check audio duration and warn if too long"""
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    audio.close()
    return duration

def time_to_seconds(time_obj):
    """Convert datetime.time object to total seconds"""
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds