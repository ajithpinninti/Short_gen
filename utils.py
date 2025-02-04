#############################
# utils.py
#############################
import os
from moviepy.audio.io.AudioFileClip import AudioFileClip

def validate_inputs(image_dir, script_path, audio_path):
    """Validate input files existence and format"""
    if not os.path.isdir(image_dir):
        return False
    if not os.path.isfile(script_path):
        return False
    if not os.path.isfile(audio_path):
        return False
    return True

def check_audio_duration(audio_path):
    """Check audio duration and warn if too long"""
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    audio.close()
    return duration

def time_to_seconds(time_obj):
    """Convert datetime.time object to total seconds"""
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds