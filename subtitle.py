import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw

def create_rounded_rect_image(size, bg_color, radius):
    """
    Create a PIL image with a rounded rectangle background.
    """
    w, h = size
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color)
    return image

def create_rounded_text_clip(text, font_name, fontsize, text_color,
                             bg_color, stroke_color, stroke_width,
                             padding=10, radius=20, method="caption"):
    """
    Render text over a rounded rectangle background.
    Returns a CompositeVideoClip.
    """
    # Create the text clip (transparent background)
    text_clip = TextClip(text=text,
                         font=font_name,
                         font_size=fontsize,
                         color=text_color,
                         stroke_color=stroke_color,
                         stroke_width=stroke_width,
                         bg_color=None)
    
    # Compute background size (adding padding)
    txt_w, txt_h = text_clip.w, text_clip.h
    bg_w = txt_w + 2 * padding
    bg_h = txt_h + 2 * padding

    # Create the rounded rectangle background using Pillow
    bg_image = create_rounded_rect_image((bg_w, bg_h), bg_color, radius)
    bg_arr = np.array(bg_image)
    duration = text_clip.duration if getattr(text_clip, "duration", None) else 0.1

    # MoviePy ImageClip requires a separate mask if there’s an alpha channel.
    if bg_arr.shape[2] == 4:
        rgb_arr = bg_arr[..., :3]
        alpha_arr = bg_arr[..., 3] / 255.0
        bg_clip = ImageClip(rgb_arr).with_duration(duration)
        mask_clip = ImageClip(alpha_arr, is_mask=True).with_duration(duration)
        bg_clip = bg_clip.with_mask(mask_clip)
    else:
        bg_clip = ImageClip(bg_arr).with_duration(duration)
    
    # Overlay the text on the background (positioned with the given padding)
    text_clip = text_clip.with_position((padding, padding))
    composite_clip = CompositeVideoClip([bg_clip, text_clip], size=(bg_w, bg_h))
    # Remove the mask so that the clip can be overlaid easily.
    composite_clip = composite_clip.without_mask()
    return composite_clip

def create_sentence_subtitle_clip(segment, sub_position, max_line_width=1000):
    """
    Create one composite subtitle clip for an entire sentence (or segment).
    The static text (all words rendered with the "context" style) remains on
    screen for the full duration of the sentence. Then, for each word, a red
    highlight (current style) overlay is added for that word’s timing.
    
    Parameters:
      segment       -- A dict containing at least a key 'words' which is a list of
                       word dicts (each with 'text', 'start', 'end').
      sub_position  -- Vertical position (or a tuple) for the subtitle.
      max_line_width-- Maximum width (in pixels) for a single line.
    
    Returns:
      A CompositeVideoClip representing the full sentence with dynamic highlighting.
    """
    # --- Settings ---
    font_name = r"fonts/Arial.otf"  # Change to your font path/name
    # (If you want no size change, you can set both to the same value.)
    context_fontsize = 50  # for the static (non-highlighted) words
    current_fontsize = 60  # for the highlighted word
    stroke_color = 'black'
    stroke_width = 2
    word_spacing = 0    # horizontal spacing between words
    line_spacing = 5    # vertical spacing between lines

    # Colors (RGBA tuples)
    context_bg = (0, 0, 0, 50)       # semi-transparent dark for context words
    current_bg = (255, 0, 0, 255)      # solid red for the current word

    words = segment['words']
    
    # Compute the overall segment (sentence) timing.
    segment_start = min(word['start'] for word in words)
    segment_end   = max(word['end'] for word in words)
    segment_duration = segment_end - segment_start

    # --- 1. Create Static Base: Render ALL words with context style ---
    static_word_clips = []
    for word in words:
        clip = create_rounded_text_clip(
            text=word['text'],
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
        static_word_clips.append(clip)

    # Arrange the static word clips into one or more lines (wrap if needed).
    lines = []       # each line is a list of clips
    current_line = []
    current_line_width = 0
    for clip in static_word_clips:
        clip_width = clip.w
        # If adding this clip would exceed the max_line_width, start a new line.
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
    
    # Determine composite dimensions and record each word’s (x, y) position.
    composite_width = max(
        sum(clip.w for clip in line) + word_spacing * (len(line) - 1)
        for line in lines
    )
    composite_height = 0
    word_positions = []  # list of tuples: (x, y, width, height)
    y_offset = 0
    for line in lines:
        line_height = max(clip.h for clip in line)
        line_width = sum(clip.w for clip in line) + word_spacing * (len(line) - 1)
        x_offset = (composite_width - line_width) / 2  # center this line horizontally
        for clip in line:
            word_positions.append((x_offset, y_offset, clip.w, clip.h))
            x_offset += clip.w + word_spacing
        y_offset += line_height + line_spacing
    composite_height = y_offset - (line_spacing if lines else 0)

    # Create a background clip for the sentence (you can change the color as desired).
    # (Note: ColorClip uses an RGB tuple; if you need transparency, you could prepare an ImageClip.)
    sentence_bg = ColorClip(size=(int(composite_width), int(composite_height)),
                            color=(0, 0, 0)).with_duration(segment_duration)

    # Place the static word clips at their recorded positions.
    static_clips = []
    # (Assume the ordering of static_word_clips matches word_positions.)
    for pos, clip in zip(word_positions, static_word_clips):
        static_clips.append(clip.with_position((pos[0], pos[1])))

    # Composite the static sentence (background + all words)
    static_sentence = CompositeVideoClip(
        [sentence_bg] + static_clips,
        size=(int(composite_width), int(composite_height))
    ).with_duration(segment_duration)

    # --- 2. Create Animated Red Overlays: one per word ---
    red_overlays = []
    for i, word in enumerate(words):
        # Create the red highlighted clip (using current style)
        red_clip = create_rounded_text_clip(
            text=word['text'],
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
        # For a smooth overlay, center the red clip on top of the corresponding static word.
        x_static, y_static, w_static, h_static = word_positions[i]
        w_red, h_red = red_clip.w, red_clip.h
        # Compute offset so that the centers match:
        offset_x = x_static + (w_static - w_red) / 2
        offset_y = y_static + (h_static - h_red) / 2
        red_clip = red_clip.with_position((offset_x, offset_y))
        # Set the red clip’s timing relative to the sentence start.
        red_start = word['start'] - segment_start
        red_duration = word['end'] - word['start']
        red_clip = red_clip.with_start(red_start).with_duration(red_duration)
        red_overlays.append(red_clip)

    # --- 3. Final Composite: Static sentence plus red overlays ---
    final_sentence = CompositeVideoClip(
        [static_sentence] + red_overlays,
        size=(int(composite_width), int(composite_height))
    )
    # Position the entire sentence composite at the desired subtitle position,
    # and set its start time relative to the global timeline.
    final_sentence = final_sentence.with_position(('center', sub_position)) \
                                   .with_start(segment_start) \
                                   .with_duration(segment_duration)
    return final_sentence

def create_subtitles(aligned_data, sub_position, max_line_width=500):
    """
    For each segment in the alignment data, create one subtitle clip (covering the
    full sentence) that remains on screen for the entire sentence duration. Within
    that clip, the red highlight (indicating the current word) is animated.
    """
    subtitle_clips = []
    for segment in aligned_data:
        clip = create_sentence_subtitle_clip(segment, sub_position, max_line_width)
        subtitle_clips.append(clip)
    return subtitle_clips
