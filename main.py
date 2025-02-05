#############################
# main.py (Entry Point)
#############################
import argparse
from video_processor import process_video
from audio_processor import process_audio
from utils import validate_inputs, check_audio_duration

def main():
    parser = argparse.ArgumentParser(description='Create Social Media Shorts')
    parser.add_argument('--images', type=str, required=True, help='Path to images directory')
    parser.add_argument('--script', type=str, required=True, help='Path to script file')
    parser.add_argument('--audio', type=str, required=True, help='Path to audio file')
    parser.add_argument('--output', type=str, default='output.mp4', help='Output file path')
    parser.add_argument('--sub_pos', type=str, default=50, help='Subtitle vertical position percentage')
    
    print("looking into arguments")
    args = parser.parse_args()
    print("arguments are: ", args)

    if not validate_inputs(args.images, args.script, args.audio):
        raise ValueError("Invalid input files")

    audio_duration = check_audio_duration(args.audio)
    if audio_duration > 40:
        print("Warning: Audio exceeds 40 seconds - platform limits may apply")

    processed_audio = process_audio(args.audio, args.script)
    process_video(args.images, args.script, processed_audio,
                 args.output, args.sub_pos,1.5)


if __name__ == "__main__":
    main()



