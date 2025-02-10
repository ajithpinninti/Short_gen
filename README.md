# Shorts Generation using Python
1. Generating the shorts as an end-to-end process based on the user input. User prompts (e.g short Mahabharat story), have to create the short video having voice-over effects and stylish subtitles for attracting the public.

2. This repository contains a tool to generate videos with scrolling subtitles by combining images, a script, and audio. The tool uses OpenAI's Whisper AI for accurate speech-to-text and provides dynamic word-level subtitle animations.

## Table of Contents

- [Installation](#installation)
- [Setting Up Virtual Environment](#setting-up-virtual-environment)
- [Installing Requirements](#installing-requirements)
- [Installing ffmpeg on Windows](#installing-ffmpeg-on-windows)
- [How to Run](#how-to-run)
- [Testing](#testing)
- [Notes](#notes)
- [Key Features](#key-features)

## Installation

Follow the steps below to set up the project on your machine.

### Setting Up Virtual Environment

Create and activate a virtual environment using the following commands:

```bash
# Create a virtual environment named "venv"
python -m venv venv

# Activate the virtual environment:
# On Windows:
venv\Scripts\activate

# On macOS and Ubuntu:
source venv/bin/activate
```

### Installing Requirements

Once your virtual environment is activated, install the required packages.

If you have a `requirements.txt` file, run:

```bash
pip install -r requirements.txt
```


### Installing ffmpeg on Windows

The tool requires `ffmpeg` for video processing. To install ffmpeg on Windows, follow these steps:

1. **Manual Installation:**
   - Visit the [ffmpeg download page](https://ffmpeg.org/download.html#build-windows).
   - Download the latest release for Windows (e.g., the latest tar.xz file).

2. **Using Chocolatey:**
   - If you have [Chocolatey](https://chocolatey.org/) installed, open an administrative command prompt and run:

     ```bash
     choco install ffmpeg-full
     choco install ffmpeg
     ```

### Installing ffmpeg on Ubantu
2. **Using Chocolatey:**
   - If you have [snap](https://https://snapcraft.io/) installed, open an administrative command prompt and run:

     ```bash
     sudo snap install ffmpeg
     ```

## How to Run

After installation, run the application using the following command. Replace the file paths with the correct paths to your resources.

For Ubuntu:

```bash
python main.py --input ./input/project --output ./outputs/video.mp4 --sub_pos 60 --train 1
```

For Windows, the command structure is similar:

```bash
python main.py --input ./input/project --output ./outputs/video.mp4 --sub_pos 60
```



Alternatively, if you are using Visual Studio Code, you can update your `launch.json` with the testing configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run main.py with args",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": false,
            "args": [
                "--input", "./input/project",
                "--output", "./outputs/video.mp4",
                "--sub_pos", "30"
            ]
        }
    ]
}
```

## Notes

- **Images:**  
  - Images should be named numerically (e.g., `1.jpg`, `2.png`, etc.).
  - There must be a corresponding image for every sentence in the script.
  - Each image is transitioned per sentence in the script.

- **Script:**  
  - The script file should have one sentence per line, ending with a full stop.
  
- **Audio:**  
  - Supported formats include MP3, WAV, OGG, etc.

- **Output:**  
  - The generated video uses H.264 for video encoding and AAC for audio to ensure broad compatibility.

- **Subtitle Position:**  
  - The subtitle position is calculated from the top of the screen (e.g., `60` means 60% from the top).

## Key Features

- **Modular Architecture:**  
  Separate components for audio and video processing.

- **Whisper AI Integration:**  
  Accurate speech-to-text conversion using OpenAI's Whisper.

- **Dynamic Subtitle Animation:**  
  Word-level subtitle animation synchronized with audio.

- **Image Sequencing:**  
  Images are sequenced based on the structure of the script.

- **Configurable Subtitle Positioning:**  
  Customize where the subtitles appear on the video.

- **Input Validation and Error Checking:**  
  Ensures reliable processing of inputs.

- **9:16 Aspect Ratio Support:**  
  Suitable for mobile-friendly vertical videos.

- **Cross-Format Compatibility:**  
  Supports various audio and image file formats.

---

Happy coding and enjoy creating your videos with scrolling subtitles!

