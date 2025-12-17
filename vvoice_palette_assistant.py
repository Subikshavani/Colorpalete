from PIL import Image, ImageDraw
import numpy as np
from collections import Counter
import os

# ---------------------------------------------------
# Helper: RGB to HEX
# ---------------------------------------------------
def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

# ---------------------------------------------------
# Extract Colors
# ---------------------------------------------------
def extract_palette(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((150, 150))

    pixels = np.array(img).reshape(-1, 3)
    counter = Counter([tuple(pixel) for pixel in pixels])

    top_colors = counter.most_common(5)
    return [color for color, count in top_colors]

# ---------------------------------------------------
# Save Palette Image
# ---------------------------------------------------
def save_palette_image(colors, output_path="palette.png"):
    width = 300
    height = 50
    palette_img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(palette_img)
    block_width = width // len(colors)

    for i, color in enumerate(colors):
        draw.rectangle([i*block_width, 0, (i+1)*block_width, height], fill=color)

    palette_img.save(output_path)
    print(f"Palette saved as {output_path}")

# ---------------------------------------------------
# Display palette in terminal with HEX labels
# ---------------------------------------------------
def display_palette_terminal(colors):
    print("\nTerminal Color Preview:")
    for color in colors:
        r, g, b = color
        hex_code = rgb_to_hex(color)
        block = f"\033[48;2;{r};{g};{b}m {hex_code} \033[0m"
        print(block, end="  ")
    print("\n")  # new line after blocks

# ---------------------------------------------------
# Main Assistant
# ---------------------------------------------------
def assistant():
    print("Text Color Palette Assistant")
    print("Type 'exit' to quit.\n")

    while True:
        filename = input("Enter image filename (with extension, e.g., a.jpg): ").strip()

        if filename.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not os.path.isfile(filename):
            print(f"File not found: {filename}")
            continue

        try:
            palette = extract_palette(filename)
            
            print("\n🎨 Top 5 Colors (RGB + HEX):")
            for c in palette:
                print(f"RGB: {c}, HEX: {rgb_to_hex(c)}")

            display_palette_terminal(palette)
            save_palette_image(palette)

        except Exception as e:
            print("Something went wrong:", e)

assistant()
