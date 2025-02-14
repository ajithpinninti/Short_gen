#############################
# main.py (Entry Point)
#############################
import argparse
from video_processor import process_video
from audio_processor import process_audio
from utils import validate_inputs, check_audio_duration
import os

def main():
    parser = argparse.ArgumentParser(description='Create Social Media Shorts')
    parser.add_argument('--input', type=str, default='input', help='Input directory path')
    parser.add_argument('--output', type=str, default='outputs/output.mp4', help='Output file path')
    parser.add_argument('--sub_pos', type=str, default="center", help='Subtitle vertical position percentage(0-100  -->  top-bottom)')
    parser.add_argument('--pbspeed', type=float, default=1.0, help='Playback speed factor')
    parser.add_argument('--train', type=int, default=0, help='For the audio training')
    
    print("looking into arguments")
    args = parser.parse_args()
    print("arguments are: ", args)

    status = validate_inputs(args.input)
    
    if status is None:
        raise ValueError("Invalid input files")
    else:
        imgs_dir, foreaudio_dir, backauido_dir, script_dir = status

    audio_duration = check_audio_duration(foreaudio_dir)
    if audio_duration > 40:
        print("Warning: Audio exceeds 40 seconds - platform limits may apply")
    
    # Count number of images in directory
    num_images = len([f for f in os.listdir(imgs_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    # Count number of lines in script
    with open(script_dir, 'r') as f:
        num_lines = sum(1 for line in f if line.strip())
        
    if num_images < num_lines:
        raise ValueError(f"Not enough images ({num_images}) for script lines ({num_lines}). Each line needs a corresponding image.")
    elif num_images > num_lines:
        raise ValueError(f"Warning: More images ({num_images}) than script lines ({num_lines}). Extra images will be ignored.")

    processed_audio = process_audio(foreaudio_dir, script_dir, args.train, backauido_dir)
    process_video(imgs_dir, script_dir, processed_audio,
                 args.output, args.sub_pos,args.pbspeed, background_volume=0.3)


if __name__ == "__main__":
    main()



