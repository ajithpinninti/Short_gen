import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw

def create_rounded_rect_image(size, bg_color, radius):
    """
    Create a PIL image of the given size with a rounded rectangle of the specified
    background color and corner radius.
    """
    w, h = size
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color)
    return image

def create_rounded_background(size, color, radius):
    """
    Create a rounded rectangle ImageClip of the given size and color.
    """
    bg_image = create_rounded_rect_image(size, color, radius)
    bg_arr = np.array(bg_image)
    if bg_arr.shape[2] == 4:
        rgb = bg_arr[..., :3]
        alpha = bg_arr[..., 3] / 255.0
        clip = ImageClip(rgb)
        mask = ImageClip(alpha, is_mask=True)
        clip.mask = mask
    else:
        clip = ImageClip(bg_arr)
    return clip

def create_subtitles(aligned_data, sub_position, max_line_width=500):
    """
    Generate subtitles where the entire sentence is displayed statically, and only the current word's background highlights.
    """
    subtitle_clips = []
    font_name = "fonts/Arial.otf"
    current_fontsize = 60
    stroke_color = 'black'
    stroke_width = 2  # Define stroke width here for padding calculation
    word_spacing = 0
    line_spacing = 5
    padding = 10 + stroke_width  # Adjust padding to account for stroke width
    radius = 20
    context_bg_color = (0, 0, 0, 50)
    current_bg_color = (255, 0, 0, 255)

    for segment in aligned_data:
        words = segment.get('words', [])
        if not words:
            continue

        sentence_start = min(word['start'] for word in words)
        sentence_end = max(word['end'] for word in words)
        duration = sentence_end - sentence_start

        word_infos = []
        for word in words:
            text = word['text']
            start = word['start']
            end = word['end']

            text_clip = TextClip(
                text=text,
                font=font_name,
                font_size=current_fontsize,
                color='white',
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                # method='caption'
            )
            text_w, text_h = text_clip.size
            bg_width = text_w + 2 * padding  # Adjusted padding includes stroke
            bg_height = text_h + 2 * padding

            context_bg = create_rounded_background((bg_width, bg_height), context_bg_color, radius)
            current_bg = create_rounded_background((bg_width, bg_height), current_bg_color, radius)

            word_info = {
                'text_clip': text_clip,
                'context_bg': context_bg,
                'current_bg': current_bg,
                'bg_width': bg_width,
                'bg_height': bg_height,
                'start': start,
                'end': end
            }
            word_infos.append(word_info)

        lines = []
        current_line = []
        current_line_width = 0

        for word_info in word_infos:
            bg_width = word_info['bg_width']
            if current_line:
                tentative_width = current_line_width + word_spacing + bg_width
            else:
                tentative_width = bg_width

            if tentative_width > max_line_width:
                lines.append(current_line)
                current_line = [word_info]
                current_line_width = bg_width
            else:
                if current_line:
                    current_line_width += word_spacing + bg_width
                else:
                    current_line_width = bg_width
                current_line.append(word_info)

        if current_line:
            lines.append(current_line)

        composite_width = 0
        composite_height = 0
        for line in lines:
            line_width = sum(word['bg_width'] for word in line) + word_spacing * (len(line) - 1)
            composite_width = max(composite_width, line_width)
            max_line_height = max(word['bg_height'] for word in line)
            composite_height += max_line_height + line_spacing
        composite_height -= line_spacing


        clips = []
        y_offset = 0
        for line in lines:
            max_line_height = max(word['bg_height'] for word in line)
            line_width = sum(word['bg_width'] for word in line) + word_spacing * (len(line) - 1)
            x_offset = (composite_width - line_width) / 2

            for word_info in line:
                context_bg = word_info['context_bg'].with_position((x_offset, y_offset)).with_duration(duration)
                clips.append(context_bg)

                current_bg_start = word_info['start'] - sentence_start
                current_bg_end = word_info['end'] - sentence_start
                current_bg = word_info['current_bg'].with_position((x_offset, y_offset))
                current_bg = current_bg.with_start(current_bg_start).with_end(current_bg_end)
                clips.append(current_bg)

                text_x = x_offset + padding
                text_y = y_offset + padding
                text_clip = word_info['text_clip'].with_position((text_x, text_y)).with_duration(duration)
                clips.append(text_clip)

                x_offset += word_info['bg_width'] + word_spacing

            y_offset += max_line_height + line_spacing

        composite_clip = CompositeVideoClip(clips, size=(composite_width, composite_height)).with_duration(duration)
        composite_clip = composite_clip.with_position(('center', sub_position)).with_start(sentence_start)
        subtitle_clips.append(composite_clip)

    return subtitle_clips