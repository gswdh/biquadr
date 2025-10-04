#!/usr/bin/env python3
"""Create a very simple, distinctive icon for Biquadr."""

from PIL import Image, ImageDraw, ImageFont
import os


def create_simple_icon():
    """Create a very simple, distinctive icon."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Create a bright red square background - very distinctive
    margin = 20
    bg_rect = [margin, margin, size - margin, size - margin]
    draw.rectangle(bg_rect, fill=(255, 0, 0, 255))  # Bright red

    # Add a large white "B" in the center
    try:
        font_size = 120
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Center the "B"
    text_bbox = draw.textbbox((0, 0), "B", font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - 10  # Slight adjustment for centering

    draw.text((text_x, text_y), "B", fill=(255, 255, 255, 255), font=font)

    # Save as PNG
    img.save("biquadr_icon.png", "PNG")
    print("✅ Created simple biquadr_icon.png")

    # Also create ICO
    img.save("biquadr_icon.ico", format="ICO")
    print("✅ Created simple biquadr_icon.ico")


if __name__ == "__main__":
    create_simple_icon()
