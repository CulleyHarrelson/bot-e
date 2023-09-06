from PIL import Image, ImageDraw, ImageFont


def create_meme(image_path, top_text, bottom_text, output_path):
    with Image.open(image_path) as img:
        width, height = img.size

        # Load a font for the meme text
        font = ImageFont.load_default()

        # Create a drawing context
        draw = ImageDraw.Draw(img)

        # Calculate bounding boxes for top and bottom text
        top_text_bbox = draw.textbbox((0, 0), top_text, font=font)
        bottom_text_bbox = draw.textbbox((0, 0), bottom_text, font=font)

        # Calculate positions for top and bottom text
        top_text_x = (width - (top_text_bbox[2] - top_text_bbox[0])) // 2
        top_text_y = 10
        bottom_text_x = (width - (bottom_text_bbox[2] - bottom_text_bbox[0])) // 2
        bottom_text_y = height - (bottom_text_bbox[3] - bottom_text_bbox[1]) - 10

        # Draw top and bottom text on the image
        draw.text((top_text_x, top_text_y), top_text, font=font, fill="white")
        draw.text((bottom_text_x, bottom_text_y), bottom_text, font=font, fill="white")

        # Save the modified image
        img.save(output_path)


# Example usage
input_image_path = "4253978046.png"
output_image_path = "output_meme.png"
top_text = "The Fickle World of Flaky Friends"
bottom_text = "Event Planning Woes"
create_meme(input_image_path, top_text, bottom_text, output_image_path)
print(f"Meme created. Output image saved as: {output_image_path}")
