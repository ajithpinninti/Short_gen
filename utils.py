#############################
# utils.py
#############################
import os
from moviepy.audio.io.AudioFileClip import AudioFileClip

import os

def validate_inputs(input_dir):
    """Validate input files existence and format"""
    image_dir = os.path.join(input_dir, "images/")
    script_path = os.path.join(input_dir, "script.txt")
    audio_dir = os.path.join(input_dir, "audio")
    allowed_audio_formats = {".mp3", ".wav", ".ogg"}

    # Validate if the "images" directory exists
    if not os.path.isdir(image_dir):
        print("Image directory not found")
        return None
    
    if not os.path.isfile(script_path):
        print("Script file not found")
        return None
    
    # Validate if the "audio" directory exists and contains at least one allowed audio file
    if not os.path.isdir(audio_dir):
        print("Audio directory not found")
        return None
    
    # Check for voiceover and background audio files
    foreaudio_dir = None
    backauido_dir = None
    
    for f in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, f)
        if os.path.isfile(file_path) and os.path.splitext(f)[1].lower() in allowed_audio_formats:
            # Check filename for voiceover or background
            filename = os.path.splitext(f)[0].lower()
            if "voiceover" in filename or "voice" in filename:
                foreaudio_dir = file_path
            elif "background" in filename or "bg" in filename:
                backauido_dir = file_path
    
    if foreaudio_dir is None:
        print("No voiceover audio file found")
        return None

    if backauido_dir is None:
        print("No background audio file found")
        return None

    audio_dir_file = None
    for f in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, f)
        if os.path.isfile(file_path) and os.path.splitext(f)[1].lower() in allowed_audio_formats:
            audio_dir_file = file_path
    
    if audio_dir_file is None:
        print("No valid audio file found in the audio directory")
        return None

    return [image_dir, foreaudio_dir, backauido_dir, script_path]

def check_audio_duration(audio_path):
    """Check audio duration and warn if too long"""
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    audio.close()
    return duration

def time_to_seconds(time_obj):
    """Convert datetime.time object to total seconds"""
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds