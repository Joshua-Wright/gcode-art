from math import sin, cos, pi, sqrt, fmod

from PIL import Image
from PIL import ImageOps

from gcode import PolargraphKinematics, CartesianKinematics, Kinematics
from image_kinematics import ImageKinematics

# TODO support non-square images to preserve aspect ratio

def image_to_waves(im: Image, kinematics: Kinematics, line_height: float, r: float):
    line_segment_length = 1  # mm
    print(f"r: {r}")
    print(f"2*r: {2*r}")

    n_lines = 2 * int(2 * r / line_height)
    n_segments = int(2 * r / line_segment_length)

    # draw a bounding box
    # C-------B
    # |       |
    # |   O---A
    # |       |
    # D-------E
    kinematics.travel(0, 0)  # O
    kinematics.travel(r, 0)  # A
    kinematics.move(r, r)  # B
    kinematics.move(-r, r)  # C
    kinematics.move(-r, -r)  # D
    kinematics.move(r, -r)  # E
    # but start in the top-left corner
    kinematics.move(r, r)  # B
    kinematics.move(-r, r)  # C

    print('image size: ' + str(im.size))

    im = im.convert('L')
    im = im.resize((n_segments, n_lines))
    im = ImageOps.autocontrast(im)
    image_width, image_height = im.size
    im.save('test.png')


    def image_to_gcode_coordinates(xi: int, yi: int):
        x = float(xi)
        y = float(yi)

        x -= image_width / 2
        x /= image_width
        x *= 2 * r

        y = image_height - y
        y -= image_height / 2
        y /= image_height
        y *= 2 * r

        return x, y


    print('n_segments', n_segments)
    print('n_lines', n_lines)

    for yi in range(0, n_lines, 2):
        for xi in range(n_segments):
            image_y_offset = int(xi % 2 == 1)
            scaled_pixel = 1 - im.getpixel((xi, yi + image_y_offset)) / 255.0
            x, y = image_to_gcode_coordinates(xi, yi)
            y -= line_height / 2

            y_offset = scaled_pixel * line_height / 2
            if xi % 2 == 1:
                y_offset *= -1

            kinematics.move(x, y + y_offset)
        # move around the border to the next line
        x, y = image_to_gcode_coordinates(image_width, yi)
        kinematics.move(r, y - line_height / 2)  # A on current line
        kinematics.move(r, r)  # B
        kinematics.move(-r, r)  # C
        kinematics.move(*image_to_gcode_coordinates(0, yi + 1))  # C on next line

if __name__ == '__main__':
    line_height = 12  # mm
    r = line_height * 23.5

    kinematics = ImageKinematics(
        PolargraphKinematics(
            top_clip_distance=1340,
            wire_length=900,
            max_feedrate=5000,
            max_acceleration=25,
        ),
        pixels_per_mm=2,
        line_thickness_mm=1,
    )

    filename = 'images/Bulbasaur.png'
    im: Image = Image.open(filename)

    image_to_waves(im, kinematics, line_height, r)
    kinematics.to_file(f"{filename}.g")
