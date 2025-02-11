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

# def create_basic_subtitles(aligned_data, sub_position):
#     """
#     Generate animated word-level subtitles with different background colors:
#       - The current word is highlighted with one background color.
#       - The previous and next words are shown in a different background color.
    
#     Each composite subtitle is shown only during the current word's time.
#     """

#     subtitle_clips = []
#     font_name = r"fonts/Arial.otf"
#     spacing = 10  # pixels between words

#     for segment in aligned_data:
#         words = segment['words']
#         # Process each word in the segment
#         for i, word in enumerate(words):
#             # Get context texts: previous and next words if available.
#             prev_text = words[i-1]['text'] if i > 0 else ""
#             current_text = word['text']
#             next_text = words[i+1]['text'] if i < len(words) - 1 else ""

#             # Create individual TextClips for each word.
#             # Previous (and next) words: use one background color.
#             context_bg = 'rgba(0, 0, 0, 128)'  # semi-transparent black for context words
#             # Current word: use a different background (highlight)
#             current_bg = 'rgba(255, 0, 0, 255)'  # semi-transparent red for the current word

#             center_font_size = 60
#             side_font_size = 50

#             prev_clip = None
#             if prev_text:
#                 prev_clip = TextClip(
#                     text=prev_text,
#                     font=font_name,
#                     font_size=side_font_size,
#                     color='white',
#                     bg_color=context_bg,
#                     stroke_color='black',
#                     stroke_width=2,
#                     # method='caption'
#                 )
#             current_clip = TextClip(
#                 text=current_text,
#                 font=font_name,
#                 font_size=center_font_size,
#                 color='white',
#                 bg_color=current_bg,
#                 stroke_color='black',
#                 stroke_width=2,
#                 # method='caption'
#             )
#             next_clip = None
#             if next_text:
#                 next_clip = TextClip(
#                     text=next_text,
#                     font=font_name,
#                     font_size=side_font_size,
#                     color='white',
#                     bg_color=context_bg,
#                     stroke_color='black',
#                     stroke_width=2,
#                     # method='caption'
#                 )

#             # Arrange the available clips horizontally.
#             x_offset = 0
#             clips = []
#             if prev_clip is not None:
#                 prev_clip = prev_clip.with_position((x_offset, 0))
#                 clips.append(prev_clip)
#                 x_offset += prev_clip.w + spacing  # add spacing after the previous word

#             current_clip = current_clip.with_position((x_offset, 0))
#             clips.append(current_clip)
#             x_offset += current_clip.w  # update x_offset after current word

#             if next_clip is not None:
#                 x_offset += spacing  # add spacing before the next word
#                 next_clip = next_clip.with_position((x_offset, 0))
#                 clips.append(next_clip)
#                 x_offset += next_clip.w

#             total_width = x_offset  # total width of the composite text clip
#             height = max(clip.h for clip in clips)  # maximum height among the clips

#             # Create a composite clip for the three words.
#             composite_clip = CompositeVideoClip(clips, size=(total_width, height))
#             composite_clip = composite_clip.with_start(word['start']) \
#                                            .with_duration(word['end'] - word['start'])
#             # Center the composite clip horizontally and use the provided vertical position.
#             composite_clip = composite_clip.with_position(('center', sub_position))
#             subtitle_clips.append(composite_clip)

#     return subtitle_clips



def process_video(image_dir, script_path, audio_data, output_path, sub_position,playback_speed):
    """Main video processing function
    playback_speed: Speedup factor for the final video 0.0 to 2.0
    """
    sub_position = int(sub_position)
    print(playback_speed, "\n\n\n")
    temp_audio = "temp/speedup_audio.mp3" # Temporary audio file for speedup
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
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


