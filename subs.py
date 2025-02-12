import numpy as np
from moviepy.video.VideoClip import ImageClip, TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw

def create_rounded_rect_image(size, bg_color, radius):
    """
    Creates a Pillow (RGBA) image of a rounded rectangle of the given size/color/radius.
    """
    w, h = size
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))  # transparent background
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=bg_color)
    return image

def create_text_clip(word_text, font_name, fontsize, color='white', stroke_color=None, stroke_width=0):
    """
    Creates a TextClip for a single word (no background).
    """
    return TextClip(
        text=word_text,
        font=font_name,
        font_size=fontsize,
        color=color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        # method='caption'  # If you like; sometimes 'label' is simpler for single words
    )

def create_highlight_clip(size, bg_color, duration, start_time, position, radius=20):
    """
    Creates a highlight clip (rounded rectangle) with the given size, color, duration, and start time.
    Placed at 'position' inside the composite. This returns *one* clip suitable for layering.
    """
    # Build a Pillow image with the desired color/size/radius
    pil_img = create_rounded_rect_image(size, bg_color, radius=radius)
    arr = np.array(pil_img)  # shape (H, W, 4)
    
    # Separate RGB and alpha
    rgb_arr = arr[..., :3]
    alpha_arr = arr[..., 3] / 255.0
    
    # Build an ImageClip for the RGB data
    highlight_rgb = ImageClip(rgb_arr).with_duration(duration)
    # Build the mask
    highlight_mask = ImageClip(alpha_arr, is_mask=True).with_duration(duration)
    # Attach mask
    highlight_clip = highlight_rgb.with_mask(highlight_mask)

    # Time-range
    highlight_clip = highlight_clip.with_start(start_time)
    
    # Position inside the composite (this doesn't override the start time)
    highlight_clip = highlight_clip.with_position(position)
    return highlight_clip

def create_subtitles(aligned_data, sub_position, max_line_width=500):
    """
    Creates a list of CompositeVideoClip objects, one per segment. Each segment
    shows *all* its words for the entire time range, with highlight rectangles
    appearing only when the corresponding word is "current".
    
    aligned_data: a list of segments, each segment is a dict:
        {
          "words": [
              {"text": "Hello", "start": 1.0, "end": 1.5},
              {"text": "world", "start": 1.5, "end": 2.0},
              ...
          ]
        }
    sub_position: vertical coordinate for placing subtitles (e.g. 800 or "bottom").
    max_line_width: max pixels per line before wrapping.
    """
    subtitle_clips = []
    
    font_name = r"fonts/Arial.otf"     # or "fonts/YourFont.ttf" 
    main_fontsize = 50
    stroke_color = 'black'
    stroke_width = 2
    word_spacing = 10
    line_spacing = 10
    
    # Colors for highlight vs normal background
    highlight_color = (255, 0, 0, 255)  # Semi-opaque red
    # If you want a global background behind all words, define something like:
    global_bg_color = (0, 0, 0, 50)  # black, but you can also do alpha here if desired.

    for segment in aligned_data:
        words = segment['words']
        if not words:
            continue
        
        # Determine the segment start/end
        segment_start = min(w['start'] for w in words)
        segment_end   = max(w['end']   for w in words)
        seg_duration  = segment_end - segment_start
        
        # 1) Create text clips for *all* words (no BG)
        word_text_clips = []
        for w in words:
            txt_clip = create_text_clip(
                w['text'],
                font_name=font_name,
                fontsize=main_fontsize,
                color='white',
                stroke_color=stroke_color,
                stroke_width=stroke_width
            ).with_duration(seg_duration)  # each text clip spans the entire segment
            word_text_clips.append((w, txt_clip))

        # 2) Arrange them in lines (like your existing logic)
        lines = []
        current_line = []
        current_line_width = 0
        
        for w, txt_clip in word_text_clips:
            clip_width = txt_clip.w
            if current_line and (current_line_width + word_spacing + clip_width > max_line_width):
                # start a new line
                lines.append(current_line)
                current_line = [(w, txt_clip)]
                current_line_width = clip_width
            else:
                if current_line:
                    current_line_width += word_spacing + clip_width
                else:
                    current_line_width = clip_width
                current_line.append((w, txt_clip))
        
        # Append last line if not empty
        if current_line:
            lines.append(current_line)
        
        # 3) Calculate total composite size
        composite_width = max(
            sum(tc.w for (_, tc) in line) + word_spacing * (len(line) - 1)
            for line in lines
        )
        composite_height = 0
        line_heights = []
        for line in lines:
            lh = max(tc.h for (_, tc) in line)
            line_heights.append(lh)
            composite_height += lh
        composite_height += line_spacing * (len(lines) - 1)
        
        # 4) Optionally create a single background for all text
        #    visible from segment_start to segment_end.
        # global_bg = (ColorClip(size=(composite_width, composite_height),
        #                        color=global_bg_color)
        #                 .with_duration(seg_duration)
        #              )
        
        # 5) Position each word + build highlight clips
        # We'll keep track of these for the CompositeVideoClip.
        positioned_text_clips = []
        highlight_clips = []
        
        y_offset = 0
        for line_idx, line in enumerate(lines):
            line_width = sum(tc.w for _, tc in line) + word_spacing * (len(line) - 1)
            x_offset = (composite_width - line_width) / 2  # center the line
            max_line_h = line_heights[line_idx]
            
            for (w, txt_clip) in line:
                # Position the text clip
                x_pos = x_offset
                y_pos = y_offset + (max_line_h - txt_clip.h)/2
                p_txt_clip = txt_clip.with_position((x_pos, y_pos))
                
                # We also create a highlight clip for this word, sized exactly to the text clip
                # plus some padding if you want a margin around the text.
                padding = 10
                highlight_w = txt_clip.w + 2*padding
                highlight_h = txt_clip.h + 2*padding
                
                # Create a highlight clip that is only visible from w['start']..w['end']
                # but the overall segment's timeline is segment_start..segment_end.
                # So we do with_start(...).
                # We place it in the same spot as the text, minus the padding.
                highlight_start = w['start']
                highlight_duration = (w['end'] - w['start'])
                
                # If your timeline is zero-based from the beginning of the segment,
                # you'll want to shift that to local time. i.e. highlight_start -= segment_start
                # but typically you can just keep absolute times if you combine everything in final.
                local_start = highlight_start - segment_start  # local time inside the segment
                
                highlight = create_highlight_clip(
                    size=(highlight_w, highlight_h),
                    bg_color=highlight_color,
                    duration=highlight_duration,
                    start_time=local_start,
                    position=(x_pos - padding, y_pos - padding),
                    radius=20
                )
                
                highlight_clips.append(highlight)
                positioned_text_clips.append(p_txt_clip)
                
                x_offset += txt_clip.w + word_spacing
            y_offset += max_line_h + line_spacing
        
        # 6) Build a CompositeVideoClip for this entire segment
        # The segment clip is "local" in time from 0..seg_duration. We'll shift it
        # to actual time later (using .with_start(segment_start)).
        seg_clip = CompositeVideoClip(
             highlight_clips + positioned_text_clips,
            size=(composite_width, composite_height)
        ).with_duration(seg_duration)
        
        # Then position it in the final video (center horizontally, sub_position vertically)
        seg_clip = seg_clip.with_position(('center', sub_position))
        # Shift the clip so it appears at the correct absolute time in the final video.
        seg_clip = seg_clip.with_start(segment_start)

        subtitle_clips.append(seg_clip)
    
    return subtitle_clips
