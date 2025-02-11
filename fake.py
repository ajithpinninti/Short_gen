import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw



def create_subtitles(aligned_data, sub_position):
    """
    Generate animated word-level subtitles with different background colors:
      - The current word is highlighted with one background color.
      - The previous and next words are shown in a different background color.
    
    Each composite subtitle is shown only during the current word's time.
    """

    subtitle_clips = []
    font_name = r"fonts/Arial.otf"
    spacing = 10  # pixels between words

    for segment in aligned_data:
        words = segment['words']
        # Process each word in the segment
        for i, word in enumerate(words):
            # Get context texts: previous and next words if available.
            prev_text = words[i-1]['text'] if i > 0 else ""
            current_text = word['text']
            next_text = words[i+1]['text'] if i < len(words) - 1 else ""

            # Create individual TextClips for each word.
            # Previous (and next) words: use one background color.
            context_bg = 'rgba(0, 0, 0, 128)'  # semi-transparent black for context words
            # Current word: use a different background (highlight)
            current_bg = 'rgba(255, 0, 0, 255)'  # semi-transparent red for the current word

            center_font_size = 60
            side_font_size = 50

            prev_clip = None
            if prev_text:
                prev_clip = TextClip(
                    text=prev_text,
                    font=font_name,
                    font_size=side_font_size,
                    color='white',
                    bg_color=context_bg,
                    stroke_color='black',
                    stroke_width=2,
                    # method='caption'
                )
            current_clip = TextClip(
                text=current_text,
                font=font_name,
                font_size=center_font_size,
                color='white',
                bg_color=current_bg,
                stroke_color='black',
                stroke_width=2,
                # method='caption'
            )
            next_clip = None
            if next_text:
                next_clip = TextClip(
                    text=next_text,
                    font=font_name,
                    font_size=side_font_size,
                    color='white',
                    bg_color=context_bg,
                    stroke_color='black',
                    stroke_width=2,
                    # method='caption'
                )

            # Arrange the available clips horizontally.
            x_offset = 0
            clips = []
            if prev_clip is not None:
                prev_clip = prev_clip.with_position((x_offset, 0))
                clips.append(prev_clip)
                x_offset += prev_clip.w + spacing  # add spacing after the previous word

            current_clip = current_clip.with_position((x_offset, 0))
            clips.append(current_clip)
            x_offset += current_clip.w  # update x_offset after current word

            if next_clip is not None:
                x_offset += spacing  # add spacing before the next word
                next_clip = next_clip.with_position((x_offset, 0))
                clips.append(next_clip)
                x_offset += next_clip.w

            total_width = x_offset  # total width of the composite text clip
            height = max(clip.h for clip in clips)  # maximum height among the clips

            # Create a composite clip for the three words.
            composite_clip = CompositeVideoClip(clips, size=(total_width, height))
            composite_clip = composite_clip.with_start(word['start']) \
                                           .with_duration(word['end'] - word['start'])
            # Center the composite clip horizontally and use the provided vertical position.
            composite_clip = composite_clip.with_position(('center', sub_position))
            subtitle_clips.append(composite_clip)

    return subtitle_clips





def create_rounded_rect_image(size, bg_color, radius):
    """
    Create a PIL image of the given size with a rounded rectangle.
    """
    w, h = size
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))  # Transparent canvas.
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color)
    return image

def create_rounded_text_clip(text, font_name, fontsize, text_color,
                             bg_color, stroke_color, stroke_width,
                             padding=10, radius=20, method="caption",
                             use_mask=True, default_duration=1):
    """
    Create a composite clip that overlays a transparent text clip on top of a
    rounded rectangle background. The composite clip's duration is explicitly set.
    """
    # (1) Create the text clip with a transparent background.
    text_clip = TextClip(
        text=text,
        font=font_name,
        font_size=fontsize,
        color=text_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        # method=method,
        bg_color=None  # Ensure transparency!
    )
    
    # Set a default duration if not provided.
    if not getattr(text_clip, "duration", None):
        text_clip = text_clip.with_duration(default_duration)
    
    # (2) Calculate dimensions.
    txt_w, txt_h = text_clip.w, text_clip.h
    bg_w = txt_w + 2 * padding
    bg_h = txt_h + 2 * padding

    # (3) Create the rounded rectangle background.
    bg_image = create_rounded_rect_image((bg_w, bg_h), bg_color, radius)
    bg_image.save("hi.png")  # For debugging; verify that hi.png looks correct.
    bg_arr = np.array(bg_image)
    
    # Use the text clip's duration.
    duration = text_clip.duration
    
    # (4) Create the background clip, using a mask if needed.
    if use_mask and bg_arr.shape[2] == 4:
        rgb_arr = bg_arr[..., :3]
        alpha_arr = bg_arr[..., 3] / 255.0  # Normalize alpha to [0,1]
        bg_clip = ImageClip(rgb_arr).with_duration(duration)
        mask_clip = ImageClip(alpha_arr, is_mask=True).with_duration(duration)
        bg_clip = bg_clip.with_mask(mask_clip)
    else:
        bg_clip = ImageClip(bg_arr).with_duration(duration)
    
    # (5) Position the text clip on top of the background.
    text_clip = text_clip.with_position((padding, padding))
    
    # (6) Create the composite clip.
    composite_clip = CompositeVideoClip([bg_clip, text_clip], size=(bg_w, bg_h))
    # **Explicitly set the duration on the composite clip:**
    composite_clip = composite_clip.with_duration(duration)
    
    return composite_clip

# Testing the function:
if __name__ == "__main__":
    # Use a fully opaque red background for testing.
    test_clip = create_rounded_text_clip(
        text="Test",
        font_name= r"fonts/Arial.otf",           # Ensure this font is available on your system.
        fontsize=50,
        text_color="white",
        bg_color=(255, 0, 0, 255),     # Fully opaque red.
        stroke_color="black",
        stroke_width=1,
        padding=10,
        radius=20,
        method="caption",
        use_mask=True,               # Use the mask to handle transparency.
        default_duration=2           # Set the duration to 2 seconds for testing.
    )
    test_clip.preview()






