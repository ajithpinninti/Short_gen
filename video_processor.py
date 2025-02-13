#############################
# video_processor.py (Updated for MoviePy 2.1.1)
#############################
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from subtitles import create_subtitles

import os
import subprocess

def create_image_clips(image_dir, aligned_data):
    """Create image clips with proper sequencing and duration"""
    images = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir)], 
                   key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    
    clips = []
    test_start = [0,4.56,9.82,6]
    test_durations = [4.2,4.58,2.44]
    for idx, segment in enumerate(aligned_data):
        if idx >= len(images):
            break
            
        # clip = ImageClip(images[idx]).with_start(test_start[idx],change_end=True)
        # clip = clip.with_duration(test_durations[idx])
        duration = segment['end'] - segment['start']        
        print(f"Segment {idx}: Start={segment['start']}, End={segment['end']}, Duration={duration}")
        clip = ImageClip(images[idx]).with_start(segment['start'],change_end=False)
        if(idx == len(aligned_data)-1):
            #final clip end with last segment end
            clip = clip.with_end(segment['end'])
        else:
            #clip end with next segment start
            clip = clip.with_end(aligned_data[idx+1]['start'])
        
        # clip = clip.with_duration(segment['end'] - segment['start'])
        # print(f"Clip {idx} duration after assignment: {clip.duration}")
        # print(f"Clip {idx} start  after assignment: {clip.start}")
        # print(f"Clip {idx} end  after assignment: {clip.end}")


        # clip.preview(fps=24)
        # print("clip duration")
        # print(idx)
        # print(clip.duration)
        clips.append(clip)  #set_start(segment['start']))
    
    return concatenate_videoclips(clips, method="chain")#"chain")


def process_video(image_dir, script_path, audio_data, output_path, sub_position, playback_speed, background_audio_path=None):
    """Main video processing function
    playback_speed: Speedup factor for the final video 0.0 to 2.0
    sub_position: Float value between 0-100 representing vertical position as percentage
    """
    # Clamp sub_position to valid range (0-100)
    sub_position = max(0, min(100, float(sub_position)))
    
    # Get video dimensions from first image
    first_image = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir)])[0]
    video_clip = ImageClip(first_image)
    video_height = video_clip.size[1]
    
    # Create subtitles first to get their height
    temp_subtitles = create_subtitles(audio_data['aligned_data'], 0)  # temporary position
    if temp_subtitles:
        # Get maximum height among all subtitle clips
        subtitle_height = max(clip.size[1] for clip in temp_subtitles)
        
        # Calculate safe position that won't go off-screen
        max_y_position = video_height - subtitle_height - 20  # 20px safety margin
        
        # Convert percentage to actual pixel position with bounds checking
        sub_position_pixels = int((sub_position / 100) * max_y_position)
    else:
        sub_position_pixels = 0
    
    # Create actual subtitles with correct position
    subtitles = create_subtitles(audio_data['aligned_data'], sub_position_pixels)
    
    print(playback_speed, "\n\n\n")
    temp_audio = "temp/speedup_audio.mp3" # Temporary audio file for speedup
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    video_clip = create_image_clips(image_dir, audio_data['aligned_data'])
    # video_clip.preview(fps=24)
    
    final_video = CompositeVideoClip([video_clip] + subtitles)
    # final_video.preview(fps=24)
    
    
    speedup_command = [
        "ffmpeg", "-i", audio_data['raw_audio_path'], "-filter:a", f"atempo={playback_speed}", "-vn", temp_audio
    ]
    subprocess.run(speedup_command, check=True)
    final_video = final_video.with_speed_scaled(playback_speed)
    final_video = final_video.with_audio(AudioFileClip(temp_audio))

    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        fps=24,
        threads=4,
        preset='fast'
    )
    os.remove(temp_audio) # Remove temporary audio file


