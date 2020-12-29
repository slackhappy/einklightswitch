import logging
import os
from datetime import datetime
from PIL import Image

logger = logging.getLogger(__name__)

# needs to have 768 total vals (256 * 3)
# based on https://stackoverflow.com/a/237193
PALETTE = [0, 0, 0, 255, 0, 0, 255, 255, 255,] + [  # black, red, white
    0,  # fill in the rest with 0s
] * 253 * 3


class ImageProcessor:
    def __init__(self, savedir):
        self.savedir = savedir

    def quantize_3color(self, image):
        palette_image = Image.new("P", (1, 1))
        palette_image.putpalette(PALETTE)
        image_rgb = image.convert("RGB")
        quantized = image_rgb.quantize(palette=palette_image)
        quantized.filename = image.filename + "-quantized"
        return quantized

    # accepts a 3-color palette image (0 = black, 1 = red, 2 = white)
    # returns two monochrome images, (b, r):
    # b is black where the palette was black, else white
    # r is black where the palette was red, else white
    def separate_3color(self, image):
        b = image.point(lambda x: 0 if x == 0 else 1, mode="1")
        b.filename = image.filename + "-b"
        r = image.point(lambda x: 0 if x == 1 else 1, mode="1")
        r.filename = image.filename + "-r"
        return (b, r)

    def save(self, image):
        path = os.path.join(self.savedir, image.filename + ".png")
        logger.debug('saving %s', path)
        image.save(path)

    # https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd2in13b_V3.py#L98
    # pack the monochrome image into one bit per pixel
    def bitpack(self, image):
        buf = [0xFF] * (int(self.width / 8) * self.height)
        for x in range(image.width):
            for y in range(image.height):
                buf[int((x + y * self.width) / 8)] &= ~(0x80 >> (x % 8))
        return buf
