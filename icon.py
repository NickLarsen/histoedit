#!/usr/bin/env python3
"""
Generate a custom histogram icon for HistoEdit
This creates a simple histogram icon that represents the app's purpose
"""

from PIL import Image, ImageDraw
import os

def create_histogram_icon():
    """Create a histogram icon for the HistoEdit app"""
    
    # Create a 128x128 image with a dark background
    size = 128
    img = Image.new('RGBA', (size, size), (40, 44, 52, 255))  # Dark theme background
    draw = ImageDraw.Draw(img)
    
    # Define colors
    primary_color = (100, 150, 255, 255)  # Blue for histogram bars
    accent_color = (255, 200, 100, 255)   # Orange for highlights
    border_color = (80, 88, 104, 255)     # Darker border
    
    # Draw border
    draw.rectangle([0, 0, size-1, size-1], outline=border_color, width=2)
    
    # Draw histogram bars (representing image editing)
    bar_width = 8
    bar_spacing = 4
    start_x = 20
    start_y = size - 30
    
    # Create a realistic histogram pattern
    bar_heights = [15, 25, 35, 45, 55, 65, 75, 85, 95, 85, 75, 65, 55, 45, 35, 25, 15]
    
    for i, height in enumerate(bar_heights):
        x = start_x + i * (bar_width + bar_spacing)
        y = start_y - height
        draw.rectangle([x, y, x + bar_width, start_y], fill=primary_color)
    
    # Add some accent bars
    accent_positions = [3, 7, 11]
    for pos in accent_positions:
        x = start_x + pos * (bar_width + bar_spacing)
        y = start_y - bar_heights[pos]
        draw.rectangle([x, y, x + bar_width, start_y], fill=accent_color)
    
    # Add a small image representation in the top-left
    draw.rectangle([10, 10, 35, 35], outline=primary_color, width=2)
    draw.rectangle([12, 12, 33, 33], fill=(60, 70, 80, 255))
    
    # Add some pixel-like squares to represent an image
    for i in range(3):
        for j in range(3):
            x = 15 + i * 5
            y = 17 + j * 5
            color = primary_color if (i + j) % 2 == 0 else accent_color
            draw.rectangle([x, y, x + 3, y + 3], fill=color)
    
    return img

def save_icon():
    """Save the icon in multiple formats"""
    icon = create_histogram_icon()
    
    # Save as PNG (for general use)
    icon.save('histoedit_icon.png')
    
    # Save as ICO (for Windows)
    icon.save('histoedit_icon.ico', format='ICO')
    
    # Save as ICNS (for macOS)
    icon.save('histoedit_icon.icns', format='ICNS')
    
    print("Icons created successfully:")
    print("- histoedit_icon.png")
    print("- histoedit_icon.ico") 
    print("- histoedit_icon.icns")

if __name__ == "__main__":
    save_icon() 