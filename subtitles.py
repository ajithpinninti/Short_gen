import numpy as np
from PIL import Image, ImageDraw
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# --------------------------------------------------------------------
# 1) Rounded Rectangle Helpers
# --------------------------------------------------------------------

def create_rounded_rect_image(size, rgba_color, radius):
    """
    Create a PIL Image (RGBA) with a rounded rectangle of `rgba_color`.
    Corners outside the rounded area are fully transparent.
    """
    w, h = size
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # Single-channel mask (0=transparent, 255=opaque)
    mask = Image.new("L", (w, h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)

    # The colored rectangle
    solid = Image.new("RGBA", (w, h), rgba_color)

    # Composite the colored rectangle through the mask
    return Image.composite(solid, base, mask)


def create_rounded_background(size, rgba_color, radius):
    """
    Returns an ImageClip shaped as a rounded rectangle with `rgba_color`.
    Preserves transparency and corner rounding via an alpha mask.
    """
    pil_img = create_rounded_rect_image(size, rgba_color, radius)
    arr = np.array(pil_img)  # shape: (H, W, 4)
    rgb   = arr[..., :3]
    alpha = arr[..., 3] / 255.0

    clip_rgb = ImageClip(rgb)
    mask_clip = ImageClip(alpha, is_mask=True)
    clip_rgb.mask = mask_clip
    return clip_rgb


# --------------------------------------------------------------------
# 2) Word Info (No Normal BG)
# --------------------------------------------------------------------

def prepare_word_info(
    text_str, w_start, w_end,
    normal_font, normal_font_size, normal_text_color, normal_stroke_color, normal_stroke_width, page_bg_color,
    highlight_font, highlight_font_size, highlight_text_color, highlight_stroke_color, highlight_stroke_width,
    highlight_bg_color, highlight_bg_radius,
    padding
):
    """
    Creates a 'word_info' dict for each word:
      - Normal text (no normal background).
      - Highlight background + highlight text.
    """
    # Normal text only (always visible)
    normal_txt = TextClip(
        text=text_str,
        font=normal_font,
        font_size=normal_font_size,
        color=normal_text_color,
        stroke_color=normal_stroke_color,
        stroke_width=normal_stroke_width,
        bg_color = page_bg_color
        # method="label"
    )
    nw, nh = normal_txt.size

    # Highlight text (only visible during [w_start, w_end])
    highlight_txt = TextClip(
        text=text_str,
        font=highlight_font,
        font_size=highlight_font_size,
        color=highlight_text_color,
        stroke_color=highlight_stroke_color,
        stroke_width=highlight_stroke_width,
        # method="label"
        bg_color = highlight_bg_color
    )
    hw, hh = highlight_txt.size
    
    # Highlight background
    highlight_bg = create_rounded_background(
        (hw + 2*padding, hh + 2*padding),
        highlight_bg_color,
        highlight_bg_radius
    )

    # We'll store the bounding boxes for normal/highlight
    word_info = {
        'text': text_str,
        'start': w_start,
        'end': w_end,

        'normal_txt': normal_txt,
        'normal_w': nw,
        'normal_h': nh,

        'highlight_txt': highlight_txt,
        'highlight_bg': highlight_bg,
        'highlight_w': hw + 2*padding,
        'highlight_h': hh + 2*padding
    }
    return word_info


# --------------------------------------------------------------------
# 3) Line Wrapping
# --------------------------------------------------------------------

def wrap_words_into_lines(word_infos, max_line_width, word_spacing, padding):
    """
    Accumulates words into lines until adding another word
    would exceed `max_line_width`. Returns a list of lines,
    where each line is a list of word_infos.

    The 'width' for each word is the max of its normal text or
    highlight box, whichever is bigger, so there's no 'jump.'
    """
    lines = []
    current_line = []
    current_width = 0

    for w in word_infos:
        # We'll compare the final bounding width if highlight is bigger
        # Normal text has no background, but highlight does:
        normal_box_w = w['normal_w']
        highlight_box_w = w['highlight_w']
        box_w = max(normal_box_w + 2*padding, highlight_box_w)
        # The +2*padding for normal text is optional if you want spacing around it as well

        if current_line:
            test_width = current_width + word_spacing + box_w
        else:
            test_width = box_w

        if test_width > max_line_width:
            lines.append(current_line)
            current_line = [w]
            current_width = box_w
        else:
            if current_line:
                current_width += (word_spacing + box_w)
            else:
                current_width = box_w
            current_line.append(w)

    if current_line:
        lines.append(current_line)

    return lines


# --------------------------------------------------------------------
# 4) Splitting Lines into Pages
# --------------------------------------------------------------------

def split_lines_into_pages(lines, max_lines_per_screen):
    """
    Given a list of lines, chunk them into pages of up to `max_lines_per_screen`.
    Returns a list of pages, where each page is a list of lines.
    """
    pages = []
    idx = 0
    total_lines = len(lines)

    while idx < total_lines:
        pages.append(lines[idx : idx + max_lines_per_screen])
        idx += max_lines_per_screen

    return pages


# --------------------------------------------------------------------
# 5) Building a CompositeVideoClip for a Single Page
# --------------------------------------------------------------------

def build_page_clip(
    chunked_lines, 
    chunk_start, chunk_end,
    word_spacing, line_spacing, padding,
    sub_position,
    page_bg_color, page_bg_radius
):
    """
    Build a CompositeVideoClip for a single 'page' of lines.
    Each word's normal text is always visible, highlight is shown 
    only in [word.start - chunk_start, word.end - chunk_start].

    We also create ONE big background rectangle for the entire page (like a 'sentence background').
    """
    chunk_duration = chunk_end - chunk_start

    # 1) Determine total needed width & height for this page
    max_width = 0
    total_height = 0

    for line in chunked_lines:
        # line width
        line_width = 0
        line_height = 0

        for w in line:
            # Normal text bounding box
            normal_box_w = w['normal_w'] + 2*padding
            normal_box_h = w['normal_h'] + 2*padding

            # Highlight bounding box
            hi_box_w = w['highlight_w']
            hi_box_h = w['highlight_h']

            # Use the bigger box so it doesn't "jump"
            box_w = max(normal_box_w, hi_box_w)
            box_h = max(normal_box_h, hi_box_h)

            line_width += box_w
            line_height = max(line_height, box_h)

        line_width += word_spacing * (len(line) - 1)
        max_width = max(max_width, line_width)
        total_height += (line_height + line_spacing)

    # remove the extra line_spacing
    if total_height > 0:
        total_height -= line_spacing

    # 2) Create a single background for the entire page
    page_bg_clip = None
    if (max_width > 0) and (total_height > 0):
        page_bg_clip = create_rounded_background(
            (int(max_width), int(total_height)),
            page_bg_color,
            page_bg_radius
        ).with_duration(chunk_duration)

    # 3) Place normal text and highlight text
    page_clips = []
    if page_bg_clip:
        # By default, keep the mask so corners are truly rounded
        # If you want partial transparency, ensure alpha < 255 in `page_bg_color`.
        page_clips.append(page_bg_clip)

    y_offset = 0
    for line in chunked_lines:
        line_max_h = 0

        # Calculate the total line width to center it
        line_width = 0
        for w in line:
            normal_box_w = w['normal_w'] + 2*padding
            highlight_box_w = w['highlight_w']
            box_w = max(normal_box_w, highlight_box_w)
            line_width += box_w
        line_width += word_spacing * (len(line) - 1)

        x_offset = (max_width - line_width) / 2

        for w in line:
            # Normal bounding box
            normal_box_w = w['normal_w'] + 2*padding
            normal_box_h = w['normal_h'] + 2*padding

            # Highlight bounding box
            hi_box_w = w['highlight_w']
            hi_box_h = w['highlight_h']

            box_w = max(normal_box_w, hi_box_w)
            box_h = max(normal_box_h, hi_box_h)

            line_max_h = max(line_max_h, box_h)

            # Normal text always visible
            # We'll place it so it's vertically centered in the 'box_h' area
            normal_text_x = x_offset + (box_w - w['normal_w'])/2
            normal_text_y = y_offset + (box_h - w['normal_h'])/2

            normal_clip = w['normal_txt'].with_position((normal_text_x, normal_text_y))
            normal_clip = normal_clip.with_duration(chunk_duration)
            page_clips.append(normal_clip)

            # highlight time window
            h_start = w['start'] - chunk_start
            h_end   = w['end']   - chunk_start

            # clamp to [0, chunk_duration]
            h_start = max(0, h_start)
            h_end = min(chunk_duration, h_end)

            if h_end > h_start:
                # highlight background
                highlight_bg_clip = w['highlight_bg'].with_position((x_offset, y_offset))
                highlight_bg_clip = highlight_bg_clip.with_start(h_start).with_end(h_end)
                page_clips.append(highlight_bg_clip)

                # highlight text
                highlight_text_x = x_offset + (box_w - w['highlight_w'])/2 + padding
                highlight_text_y = y_offset + (box_h - w['highlight_h'])/2 + padding

                highlight_txt_clip = w['highlight_txt'].with_position((highlight_text_x, highlight_text_y))
                highlight_txt_clip = highlight_txt_clip.with_start(h_start).with_end(h_end)
                page_clips.append(highlight_txt_clip)

            x_offset += (box_w + word_spacing)

        y_offset += (line_max_h + line_spacing)

    # 4) Create the CompositeVideoClip
    page_comp = CompositeVideoClip(page_clips, size=(int(max_width), int(total_height)))
    page_comp = page_comp.with_duration(chunk_duration).with_start(chunk_start)
    page_comp = page_comp.with_position(('center', sub_position))

    return page_comp


# --------------------------------------------------------------------
# 6) Main Function: create_subtitles
# --------------------------------------------------------------------

def create_subtitles(
    aligned_data,
    sub_position = 'bottom',
    max_line_width=400,
    max_lines_per_screen=3,

     # Normal style (always visible)
    normal_font="fonts/Arial-bold.otf",
    normal_font_size=42,
    normal_text_color="white",
    normal_stroke_color="black",
    normal_stroke_width=2,

    # Highlight style (visible only between word.start and word.end)
    highlight_font="fonts/Arial-bold.otf",
    highlight_font_size=45,
    highlight_text_color="#42a884",
    highlight_stroke_color="black",
    highlight_stroke_width=2,
    highlight_bg_color= "#0e0f0e",
    highlight_bg_radius=10,

    # Single background color for the entire page
    page_bg_color="#0e0f0e",   # semi-transparent black
    page_bg_radius=10,

    # Layout/padding
    word_spacing=0,
    line_spacing=5,
    padding=5
):
    """
    Creates a list of subtitle 'pages' as CompositeVideoClips, each containing
    multiple lines. Instead of giving each word a normal background, we draw
    ONE big background rectangle for the entire page (like a 'sentence' or 
    'paragraph' background). Meanwhile, each word can still have a highlight
    background that appears only during [word.start, word.end].
    """
    subtitle_clips = []

    for segment in aligned_data:
        words = segment.get('words', [])
        if not words:
            continue

        # Prepare word infos for the entire segment
        word_infos = []
        for w in words:
            w_info = prepare_word_info(
                text_str=w['text'],
                w_start=w['start'],
                w_end=w['end'],
                normal_font=normal_font,
                normal_font_size=normal_font_size,
                normal_text_color=normal_text_color,
                normal_stroke_color=normal_stroke_color,
                normal_stroke_width=normal_stroke_width,
                page_bg_color = page_bg_color,
                highlight_font=highlight_font,
                highlight_font_size=highlight_font_size,
                highlight_text_color=highlight_text_color,
                highlight_stroke_color=highlight_stroke_color,
                highlight_stroke_width=highlight_stroke_width,
                highlight_bg_color=highlight_bg_color,
                highlight_bg_radius=highlight_bg_radius,
                padding=padding
            )
            word_infos.append(w_info)

        # Wrap words into lines
        lines = wrap_words_into_lines(word_infos, max_line_width, word_spacing, padding)
        if not lines:
            continue

        # Split lines into pages
        pages = split_lines_into_pages(lines, max_lines_per_screen)

        # For each page, find chunk_start & chunk_end
        for page_lines in pages:
            # earliest start / latest end among these lines
            chunk_start = min(min(w['start'] for w in line) for line in page_lines)
            chunk_end   = max(max(w['end']   for w in line) for line in page_lines)

            page_clip = build_page_clip(
                chunked_lines=page_lines,
                chunk_start=chunk_start,
                chunk_end=chunk_end,
                word_spacing=word_spacing,
                line_spacing=line_spacing,
                padding=padding,
                sub_position=sub_position,
                page_bg_color=page_bg_color,
                page_bg_radius=page_bg_radius
            )
            subtitle_clips.append(page_clip)

    return subtitle_clips
