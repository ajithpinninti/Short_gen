#############################
# video_processor.py (Updated for MoviePy 2.1.1)
#############################
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
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

def create_subtitles(aligned_data, sub_position):
    """Generate animated word-level subtitles"""
    subtitle_clips = []
    font_name = r"fonts/Arial.otf"
    for segment in aligned_data:
        words = segment['words']
        
        for word in words:
            txt_clip = TextClip(
                text=word['text'],
                font_size=70,
                font=font_name,
                color='white',
                stroke_color='black',
                stroke_width=2
            ).with_start(word['start']).with_duration(word['end'] - word['start'])
            
            txt_clip = txt_clip.with_position(('center', sub_position))
            # txt_clip.preview(fps=24)
            subtitle_clips.append(txt_clip)
    
    return subtitle_clips

def process_video(image_dir, script_path, audio_data, output_path, sub_position,playback_speed):
    """Main video processing function
    playback_speed: Speedup factor for the final video 0.0 to 2.0
    """
    sub_position = int(sub_position)
    print(playback_speed, "\n\n\n")
    temp_audio = "temp/speedup_audio.mp3" # Temporary audio file for speedup
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    
    video_clip = create_image_clips(image_dir, audio_data['aligned_data'])
    # video_clip.preview(fps=24)
    subtitles = create_subtitles(audio_data['aligned_data'], sub_position)
    
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


