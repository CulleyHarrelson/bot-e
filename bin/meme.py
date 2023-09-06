from wand.image import Image
from wand.drawing import Drawing
from wand.color import Color
import textwrap


def add_meme_area(
    image_path,
    meme_area_margin=10,
    meme_area_height=100,
    meme_text="A Dance of Names and Faces",
):
    with Image(filename=image_path) as img:
        width, height = img.width, img.height

        # Calculate meme area dimensions and position
        meme_area_width = width - 2 * meme_area_margin
        meme_area_y = height - meme_area_height - meme_area_margin

        # Composite the meme area over the original image
        with Drawing() as draw:
            # Draw the grey border
            draw.fill_color = Color("white")
            draw.stroke_color = Color("gray")
            draw.stroke_width = 2
            draw.rectangle(
                left=meme_area_margin,
                top=meme_area_y,
                right=width - meme_area_margin - 1,
                bottom=height - meme_area_margin - 1,
            )

            # Add the meme text
            draw.fill_color = Color("black")
            draw.font_size = 16
            draw.text_alignment = "center"
            draw.text(
                (width - meme_area_margin) // 2,
                height - meme_area_margin - meme_area_height // 2,
                meme_text,
            )

            draw(img)

        # Save the modified image
        output_path = "meme_" + image_path
        img.save(filename=output_path)

        return output_path


# Example usage
input_image_path = "4253978046.png"
meme_text = "A Dance of Names and Faces"
output_image_path = add_meme_area(input_image_path, meme_text=meme_text)
print(f"Meme area added. Output image saved as: {output_image_path}")
