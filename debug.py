import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw

def create_rounded_rect_image(size, bg_color, radius):
    w, h = size
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color)
    return image

def create_rounded_background(size, color, radius):
    bg_image = create_rounded_rect_image(size, color, radius)
    arr = np.array(bg_image)
    rgb = arr[..., :3]
    alpha = arr[..., 3] / 255.0
    clip_rgb = ImageClip(rgb)
    clip_alpha = ImageClip(alpha, is_mask=True)
    clip_rgb.mask = clip_alpha
    return clip_rgb

def create_subtitles_debug(aligned_data):
    # We'll skip paging & other complexities for minimal demo
    # We'll place the background at (0,0) with size big enough for all words
    # and see if we can see it.
    chunk_clips = []

    # Debug colors
    chunk_bg_color = (0, 255, 0, 255)  # Opaque GREEN background
    highlight_color = (255, 0, 0, 128) # Semi-transparent RED highlight

    # Gather all words
    if not aligned_data or not aligned_data[0].get('words'):
        return []
    words = aligned_data[0]['words']
    chunk_start = min(w['start'] for w in words)
    chunk_end   = max(w['end']   for w in words)
    chunk_duration = chunk_end - chunk_start

    # Build text clips
    padding = 15
    x_offset = 0
    y_offset = 0
    total_width = 0
    total_height = 0

    # We'll put all words on a single line for this debug
    word_clips = []
    for w in words:
        txt_clip = TextClip(text=w['text'], font="fonts/Arial.otf", font_size=60, color='white')
        w_, h_ = txt_clip.size
        # highlight rectangle
        highlight_bg = create_rounded_background((w_ + 2*padding, h_ + 2*padding), highlight_color, 10)

        word_clips.append({
            'text_clip': txt_clip,
            'highlight_bg': highlight_bg,
            'start': w['start'],
            'end': w['end'],
            'w': w_,
            'h': h_
        })
        total_width += (w_ + 2*padding)
        # single line, track max height
        if h_ + 2*padding > total_height:
            total_height = h_ + 2*padding

    # Create a big green background for entire line
    chunk_bg = create_rounded_background((total_width, total_height), chunk_bg_color, 20)
    chunk_bg = chunk_bg.with_duration(chunk_duration)

    # Add it first so everything else appears on top
    chunk_clips.append(chunk_bg)

    # Now add each word's highlight and text
    current_x = 0
    for wc in word_clips:
        # highlight visible only from (wc.start - chunk_start) to (wc.end - chunk_start)
        h_start = wc['start'] - chunk_start
        h_end   = wc['end']   - chunk_start
        if h_start < 0: h_start = 0
        if h_end > chunk_duration: h_end = chunk_duration

        if h_end > h_start:
            h_bg = wc['highlight_bg'].with_position((current_x, 0))
            h_bg = h_bg.with_start(h_start).with_end(h_end)
            chunk_clips.append(h_bg)

        # text is always visible
        t_clip = wc['text_clip'].with_position((current_x + padding, padding))
        t_clip = t_clip.with_duration(chunk_duration)
        chunk_clips.append(t_clip)

        current_x += (wc['w'] + 2*padding)

    # Build composite
    page_clip = CompositeVideoClip(chunk_clips, size=(total_width, total_height))
    page_clip = page_clip.with_start(chunk_start).with_duration(chunk_duration)
    # We'll return just this one clip
    return [page_clip]


from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy import VideoFileClip
test_data = [
  {
    "words": [
      {"text":"Hello", "start":2, "end":4},
      {"text":"Green", "start":4, "end":5},
      {"text":"Background!", "start":5, "end":7},
    ]
  }
]

clip = VideoFileClip("outputs/myvideo.mp4").subclipped(0,1)
subs = create_subtitles_debug(test_data)

final = CompositeVideoClip([clip] + subs)
final.write_videofile("debug_subs.mp4", fps=24)
