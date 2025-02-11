import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
import imageio
from PIL import Image, ImageDraw
import time

def create_rounded_rect_image(size, bg_color, radius):
    """
    Create a PIL image of the given size with a rounded rectangle of the specified
    background color and corner radius.
    
    Parameters:
      size    -- (width, height) tuple for the image size.
      bg_color-- A tuple (R, G, B, A) for the background color.
      radius  -- Corner radius in pixels.
      
    Returns:
      A PIL Image in RGBA mode.
    """
    w, h = size
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))  # fully transparent background
    draw = ImageDraw.Draw(image)
    # Draw a rounded rectangle filling the entire image.
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color)
    return image

def create_rounded_text_clip(text, font_name, fontsize, text_color,
                             bg_color, stroke_color, stroke_width,
                             padding=10, radius=20, method="caption"):
    """
    Create a MoviePy clip of text rendered over a rounded rectangle background.
    
    Parameters:
      text         -- The text string to render.
      font_name    -- Path to the font file (or font name).
      fontsize     -- Font size.
      text_color   -- Color for the text (e.g. 'white').
      bg_color     -- Background color as an (R, G, B, A) tuple.
      stroke_color -- Stroke (outline) color for the text.
      stroke_width -- Stroke width for the text.
      padding      -- Extra space (in pixels) around the text.
      radius       -- Radius for rounding the background corners.
      method       -- Method for TextClip ('caption' usually works well).
      
    Returns:
      A CompositeVideoClip with the rounded background and the text.
    """
    # Create the text clip with a transparent background.
    text_clip = TextClip(text=text,
                         font=font_name,
                         font_size=fontsize,
                         
                         color=text_color,
                         stroke_color=stroke_color,
                         stroke_width=stroke_width,
                        #  method=method,
                         bg_color=None)
    
    # Determine the size needed: add padding on all sides.
    txt_w, txt_h = text_clip.w, text_clip.h
    bg_w = txt_w + 2 * padding
    bg_h = txt_h + 2 * padding
    
    # Create the rounded rectangle background using Pillow.
    bg_image = create_rounded_rect_image((bg_w, bg_h), bg_color, radius)
    # bg_image.save("hi.png")
    # bg_clip = ImageClip(np.array(bg_image)).with_duration(
    #     text_clip.duration if hasattr(text_clip, "duration") and text_clip.duration else 0.1
    # )

    bg_arr = np.array(bg_image)  # This should be an array with shape (H, W, 4)
    duration = text_clip.duration if getattr(text_clip, "duration", None) else 0.1
    
    # Check if an alpha channel exists.
    if bg_arr.shape[2] == 4:
        # Separate RGB and alpha channels.
        rgb_arr = bg_arr[..., :3]
        alpha_arr = bg_arr[..., 3] / 255.0  # Normalize to [0, 1]
        
        # Create an ImageClip from the RGB array.
        bg_clip = ImageClip(rgb_arr).with_duration(duration)
        # Create a mask clip from the alpha channel.
        mask_clip = ImageClip(alpha_arr, is_mask=True).with_duration(duration)
        # Attach the mask to the background clip.
        bg_clip = bg_clip.with_mask(mask_clip)
    else:
        bg_clip = ImageClip(bg_arr).with_duration(duration)

    # Overlay the text on top of the background.
    text_clip = text_clip.with_position((padding, padding))

    composite_clip = CompositeVideoClip(
        [bg_clip, text_clip],
        size=(bg_w, bg_h)
    )
    composite_clip = composite_clip.without_mask()

    # **Explicitly set the duration on the composite clip:**
    # composite_clip = composite_clip.with_duration(duration)
    # composite_clip.preview()
    
    
    return composite_clip

def create_subtitles(aligned_data, sub_position, max_line_width=1000):
    """
    Generate animated word-level subtitles showing five words of context:
      - Up to 2 words preceding the current word,
      - The current word (highlighted with a rounded background),
      - Up to 2 words following the current word.
    
    If the five-word composite exceeds max_line_width, the words are split
    into multiple centered lines.
    
    Parameters:
      aligned_data  -- The alignment data, where each segment contains a list of word dicts.
                       Each word dict should have at least: 'text', 'start', and 'end'.
      sub_position  -- Vertical position in the video where subtitles will be placed.
      max_line_width-- Maximum width in pixels before breaking into a new line.
    
    Returns:
      A list of CompositeVideoClip objects that can be overlaid on the final video.
    """
    subtitle_clips = []
    font_name = r"fonts/Arial.otf"
    current_fontsize = 60
    context_fontsize = 50
    stroke_color = 'black'
    stroke_width = 2
    word_spacing = 0    # Horizontal spacing between words.
    line_spacing = 5     # Vertical spacing between lines.
    
    # Define colors as RGBA tuples.
    # Current word: semi-transparent red.
    current_bg = (255, 0, 0, 255)
    # Context words (previous and next): semi-transparent black.
    context_bg = (0, 0, 0, 50)
    
     # Sentence background parameters.
    sentence_bg_color = (0, 0, 0, 5)  # Semi-transparent black.
    sentence_bg_radius = 50

    # Process each segment from the aligned data.
    for segment in aligned_data:
        words = segment['words']
        for i, word in enumerate(words):
            # Determine a window of 3 words: up to 1 before and 1 after.
            start_index = max(0, i - 1)
            end_index = min(len(words), i + 2)  # end_index is exclusive.
            context_words = words[start_index:end_index]
            current_idx_in_context = i - start_index

            # Create a rounded text clip for each context word.
            word_clips = []
            for j, ctx_word in enumerate(context_words):
                if j == current_idx_in_context:
                    clip = create_rounded_text_clip(
                        ctx_word['text'],
                        font_name=font_name,
                        fontsize=current_fontsize,
                        text_color='white',
                        bg_color=current_bg,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        padding=10,
                        radius=20,
                        method='caption'
                    )
                else:
                    clip = create_rounded_text_clip(
                        ctx_word['text'],
                        font_name=font_name,
                        fontsize=context_fontsize,
                        text_color='white',
                        bg_color=context_bg,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        padding=10,
                        radius=20,
                        method='caption'
                    )
                    print("normal ")
                word_clips.append(clip)

            # --- Arrange the word clips into one or more lines ---
            # We build lines so that adding the next word doesn't exceed max_line_width.
            lines = []       # Each line is a list of clips.
            current_line = []
            current_line_width = 0
            
            for clip in word_clips:
                clip_width = clip.w
                # If this clip would push the line over the limit, start a new line.
                if current_line and (current_line_width + word_spacing + clip_width > max_line_width):
                    lines.append(current_line)
                    current_line = [clip]
                    current_line_width = clip_width
                else:
                    if current_line:
                        current_line_width += word_spacing + clip_width
                    else:
                        current_line_width = clip_width
                    current_line.append(clip)
            if current_line:
                lines.append(current_line)
            
            # --- Compute overall composite dimensions from the arranged lines ---
            composite_width = max(
                sum(clip.w for clip in line) + word_spacing * (len(line) - 1)
                for line in lines
            )
            composite_height = 0
            for line in lines:
                line_height = max(clip.h for clip in line)
                composite_height += line_height
            if len(lines) > 1:
                composite_height += line_spacing * (len(lines) - 1)

            # Create a black background for the entire sentence.
            sentence_bg = ColorClip(size=(composite_width, composite_height), color=(0, 0, 0))
            # Set the duration to match the subtitle's timing.
            sentence_bg = sentence_bg.with_duration(word['end'] - word['start'])
            
            
            # --- Position each clip inside the composite ---
            arranged_clips = []
            y_offset = 0
            for line in lines:
                # Calculate the total width of the line.
                line_width = sum(clip.w for clip in line) + word_spacing * (len(line) - 1)
                # Center the line horizontally within the composite.
                x_offset = (composite_width - line_width) / 2
                max_line_height = max(clip.h for clip in line)
                for clip in line:
                    arranged_clips.append(
                        clip.with_position((x_offset, y_offset + (max_line_height - clip.h) / 2))
                    )
                    x_offset += clip.w + word_spacing
                y_offset += max_line_height + line_spacing
            
            # --- Create the composite clip for this subtitle ---
            composite_clip = CompositeVideoClip([sentence_bg] +  arranged_clips, size=(composite_width, composite_height))
            # Set timing based on the current word.
            composite_clip = composite_clip.with_start(word['start']).with_duration(word['end'] - word['start'])
            # Position the composite clip at the specified subtitle vertical position.
            composite_clip = composite_clip.with_position(('center', sub_position))
            subtitle_clips.append(composite_clip)
    
    return subtitle_clips


