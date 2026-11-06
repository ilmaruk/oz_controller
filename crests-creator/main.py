import argparse
import struct
import zlib
from pathlib import Path


COLUMNS = 7
ROWS = 8
SQUARE_SIZE = 10
GAP_SIZE = 1
WIDTH = COLUMNS * SQUARE_SIZE + (COLUMNS - 1) * GAP_SIZE
HEIGHT = ROWS * SQUARE_SIZE + (ROWS - 1) * GAP_SIZE


def png_chunk(chunk_type, data):
    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk))


def generate_png(output_path):
    pixels = bytearray()
    for y in range(HEIGHT):
        pixels.append(0)
        for x in range(WIDTH):
            square_x = x % (SQUARE_SIZE + GAP_SIZE)
            square_y = y % (SQUARE_SIZE + GAP_SIZE)
            is_square = square_x < SQUARE_SIZE and square_y < SQUARE_SIZE
            is_circle = (
                is_square
                and (square_x - (SQUARE_SIZE - 1) / 2) ** 2
                + (square_y - (SQUARE_SIZE - 1) / 2) ** 2
                <= ((SQUARE_SIZE - 1) / 2) ** 2
            )
            color = (
                b"\xff\x00\x00"
                if is_circle
                else b"\x00\x00\x00"
                if is_square
                else b"\xff\xff\xff"
            )
            pixels.extend(color)

    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    png_data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(pixels))
        + png_chunk(b"IEND", b"")
    )
    Path(output_path).write_bytes(png_data)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a 76x87 PNG grid of 56 black squares with red circles."
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("crest-template.png"),
        help="output PNG path (default: crest-template.png beside this script)",
    )
    args = parser.parse_args()
    generate_png(args.output)
    print(f"Generated {WIDTH}x{HEIGHT} PNG: {args.output}")


if __name__ == "__main__":
    main()
