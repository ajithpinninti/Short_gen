import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw

def create_rounded_rect_image(size, bg_color, radius):
    """
    Create a PIL image (RGBA) of the given size with a rounded rectangle
    of the specified bg_color and corner radius.
    """
    w, h = size
    image = Image.new("RGBA", (w, h), (250, 0, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color, width=5)
    return image

def create_rounded_background(size, color, radius):
    """
    Create a rounded rectangle ImageClip of the given size and color.
    Splits it into (RGB + alpha) so MoviePy can handle transparency.
    """
    bg_image = create_rounded_rect_image(size, color, radius)
    bg_arr = np.array(bg_image)  # shape: (H, W, 4) -> RGBA
    rgb = bg_arr[..., :3]
    alpha = bg_arr[..., 3] / 255.0

    clip_rgb = ImageClip(rgb)
    clip_alpha = ImageClip(alpha, is_mask=True)
    clip_rgb.mask = clip_alpha
    return clip_rgb

def create_subtitles(
    aligned_data,
    sub_position,
    max_line_width=500,
    max_lines_per_screen=2,
    font_name="fonts/Arial.otf",
    font_size=60
):
    """
    Generates a list of CompositeVideoClips for each 'segment' in aligned_data.
    We remove the per-word background entirely and add ONE rounded rectangle
    for the entire "page" (which may contain multiple lines). Only the current
    word is highlighted in red during its interval.

    If lines exceed max_lines_per_screen, they'll spill over into multiple pages.

    Layers drawn for each page:
      1) A single big background for the entire text block (the "sentence" or page).
      2) A red highlight (rounded) for each word, only during [word.start, word.end].
      3) The text clips themselves on top.
    """

    subtitle_clips = []

    # Visual config
    stroke_color = 'black'
    stroke_width = 2
    word_spacing = 10
    line_spacing = 5
    padding = 10 + stroke_width
    radius = 20

    # One big background color behind the entire sentence/page
    sentence_bg_color = (0, 255, 0, 180)  # semi-opaque black
    # Red highlight for the "current" word
    highlight_color = (255, 0, 0, 255)  # fully opaque red

    for segment in aligned_data:
        words = segment.get('words', [])
        if not words:
            continue

        # Entire sentence time range
        sentence_start = min(w['start'] for w in words)
        sentence_end   = max(w['end']   for w in words)
        sentence_duration = sentence_end - sentence_start

        # 1) Prepare a simple word_info for text + highlight
        word_infos = []
        for w in words:
            text_str = w['text']
            start_t  = w['start']
            end_t    = w['end']

            # Create a text clip (no background)
            txt_clip = TextClip(
                text=text_str,
                font=font_name,
                font_size=font_size,
                color='white',
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                bg_color=None
            )
            text_w, text_h = txt_clip.size

            # Create a red highlight (rounded) sized for this word
            highlight_bg = create_rounded_background(
                (text_w + 2 * padding, text_h + 2 * padding),
                highlight_color,
                radius
            )

            word_info = {
                'text_clip': txt_clip,
                'highlight_bg': highlight_bg,
                'bg_w': text_w + 2 * padding,
                'bg_h': text_h + 2 * padding,
                'start': start_t,
                'end': end_t
            }
            word_infos.append(word_info)

        # 2) Wrap words into lines based on max_line_width
        lines = []
        current_line = []
        current_line_width = 0

        for winfo in word_infos:
            w_bg_w = winfo['bg_w']
            if current_line:
                test_width = current_line_width + word_spacing + w_bg_w
            else:
                test_width = w_bg_w

            if test_width > max_line_width:
                lines.append(current_line)
                current_line = [winfo]
                current_line_width = w_bg_w
            else:
                if current_line:
                    current_line_width += (word_spacing + w_bg_w)
                else:
                    current_line_width = w_bg_w
                current_line.append(winfo)

        # Add any leftover line
        if current_line:
            lines.append(current_line)

        # 3) Break lines into pages if exceed max_lines_per_screen
        idx = 0
        total_lines = len(lines)

        while idx < total_lines:
            chunked_lines = lines[idx : idx + max_lines_per_screen]
            idx += max_lines_per_screen

            # earliest start / latest end among words in these lines
            chunk_start = min(min(w['start'] for w in line) for line in chunked_lines)
            chunk_end   = max(max(w['end']   for w in line) for line in chunked_lines)
            chunk_duration = chunk_end - chunk_start

            # 4) Determine composite width/height for these lines
            composite_width = 0
            composite_height = 0
            for line in chunked_lines:
                line_width = sum(w['bg_w'] for w in line) + word_spacing*(len(line)-1)
                composite_width = max(composite_width, line_width)
                max_line_height = max(w['bg_h'] for w in line)
                composite_height += (max_line_height + line_spacing)
            composite_height -= line_spacing

            # 5) Build the clip list for these lines
            chunk_clips = []

            # a) One big background for the entire chunk/page
            page_bg = create_rounded_background(
                (composite_width, composite_height),
                sentence_bg_color,
                radius
            ).with_duration(chunk_duration)
            page_bg = page_bg.without_mask()
            chunk_clips.append(page_bg)

            # b) Position each line's words
            y_offset = 0
            for line in chunked_lines:
                max_line_height = max(w['bg_h'] for w in line)
                line_width = sum(w['bg_w'] for w in line) + word_spacing*(len(line)-1)
                x_offset = (composite_width - line_width) / 2

                for winfo in line:
                    # The highlight is only visible from (winfo.start-chunk_start) to (winfo.end-chunk_start)
                    h_start = winfo['start'] - chunk_start
                    h_end   = winfo['end']   - chunk_start
                    # clamp to [0, chunk_duration]
                    if h_start < 0: h_start = 0
                    if h_end   > chunk_duration: h_end = chunk_duration

                    if h_end > h_start:
                        h_bg = winfo['highlight_bg'].with_position((x_offset, y_offset))
                        h_bg = h_bg.with_start(h_start).with_end(h_end)
                        chunk_clips.append(h_bg)

                    # Text always visible
                    t_clip = winfo['text_clip'].with_position(
                        (x_offset + padding, y_offset + padding)
                    ).with_duration(chunk_duration)
                    chunk_clips.append(t_clip)

                    x_offset += (winfo['bg_w'] + word_spacing)
                y_offset += (max_line_height + line_spacing)

            # 6) Create CompositeVideoClip for this page
            page_clip = CompositeVideoClip(
                chunk_clips, size=(composite_width, composite_height)
            ).with_duration(chunk_duration)

            # Position on screen, align with timeline
            page_clip = page_clip.with_position(('center', sub_position)).with_start(chunk_start)
            subtitle_clips.append(page_clip)

    return subtitle_clips
