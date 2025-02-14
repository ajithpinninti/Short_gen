#############################
# video_processor.py (Updated for MoviePy 2.1.1)
#############################
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip, CompositeAudioClip
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

def process_video(image_dir, script_path, audio_data, output_path, sub_position, playback_speed, background_volume=0.3):
    """Main video processing function
    playback_speed: Speedup factor for the final video 0.0 to 2.0
    sub_position: Float value between 0-100 representing vertical position as percentage
    background_volume: Float value between 0-1 representing the volume of the background audio
    """
    # Clamp sub_position to valid range (0-100)
    sub_position = max(0, min(100, float(sub_position)))
    
    # Get video dimensions from the first image (to determine subtitle positions, etc.)
    first_image_path = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir)])[0]
    video_clip = ImageClip(first_image_path)
    video_height = video_clip.size[1]
    
    # Create actual subtitles with correct position
    subtitles = create_subtitles(audio_data['aligned_data'], video_height, sub_position)
    
    # Prepare temp audio file for speed-adjusted audio
    temp_audio = "temp/speedup_audio.mp3"
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Build the main clip from all images
    video_clip = create_image_clips(image_dir, audio_data['aligned_data'])

    # Combine subtitles over the video
    final_video = CompositeVideoClip([video_clip] + subtitles)

    # Step 1: Generate speed-adjusted main audio
    speedup_command = [
        "ffmpeg", "-i", audio_data['raw_audio_path'], 
        "-filter:a", f"atempo={playback_speed}", 
        "-vn", temp_audio
    ]
    subprocess.run(speedup_command, check=True)

    # Step 2: Adjust the video speed (visual only)
    final_video = final_video.with_speed_scaled(playback_speed)

    # Step 3: Now load the speed-adjusted (foreground) audio
    foreground_audio = AudioFileClip(temp_audio)
    background_audio_path = audio_data['background_music_path']

    # Prepare background audio if provided
    if background_audio_path is not None and os.path.exists(background_audio_path):
        print("background audio path exists")
        background_audio = AudioFileClip(background_audio_path)

        # Trim or loop the background audio to match final video duration
        # (Here we do a simple trim, but you can do more advanced logic if needed)
        final_duration = final_video.duration
        background_audio = background_audio.subclipped(0, min(background_audio.duration, final_duration))
        # Optionally adjust background volume. E.g., 0.3 (30% volume)
        background_audio = background_audio.with_volume_scaled(background_volume)
        # Step 4: Mix foreground + background
        mixed_audio = CompositeAudioClip([foreground_audio, background_audio])
    else:
        # No background audio, just use the foreground audio
        mixed_audio = foreground_audio

    # Attach the mixed audio to the final video
    final_video = final_video.with_audio(mixed_audio)

    # Step 5: Write the output video
    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        fps=24,
        threads=4,
        preset='fast'
    )

    # Cleanup
    if os.path.exists(temp_audio):
        os.remove(temp_audio)


