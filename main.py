#############################
# main.py (Entry Point)
#############################
import argparse
from video_processor import process_video
from audio_processor import process_audio
from utils import validate_inputs, check_audio_duration

def main():
    parser = argparse.ArgumentParser(description='Create Social Media Shorts')
    parser.add_argument('--input', type=str, default='input', help='Input directory path')
    parser.add_argument('--output', type=str, default='outputs/output.mp4', help='Output file path')
    parser.add_argument('--sub_pos', type=str, default="center", help='Subtitle vertical position percentage')
    parser.add_argument('--pbspeed', type=float, default=1.0, help='Playback speed factor')
    parser.add_argument('--train', type=int, default=0, help='For the audio training')
    
    print("looking into arguments")
    args = parser.parse_args()
    print("arguments are: ", args)

    status = validate_inputs(args.input)
    
    if status is None:
        raise ValueError("Invalid input files")
    else:
        imgs_dir, audio_dir, script_dir = status

    audio_duration = check_audio_duration(audio_dir)
    if audio_duration > 40:
        print("Warning: Audio exceeds 40 seconds - platform limits may apply")

    processed_audio = process_audio(audio_dir, script_dir, args.train)
    process_video(imgs_dir, script_dir, processed_audio,
                 args.output, args.sub_pos,args.pbspeed)


if __name__ == "__main__":
    main()



