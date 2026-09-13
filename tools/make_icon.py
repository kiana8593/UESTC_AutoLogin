#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
生成 exe 图标（可复现，改颜色/形状后重跑即可）。

用法：
    python tools/make_icon.py

产物：
    assets/icon.png   256x256，给 README 或商店页用
    assets/icon.ico   含 16/32/48/64/128/256 多尺寸，PyInstaller --icon 用这个
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
TOP = (37, 99, 235)      # 蓝
BOTTOM = (14, 165, 233)  # 天蓝
WHITE = (255, 255, 255, 255)
ASSETS = Path(__file__).resolve().parent.parent / 'assets'


def rounded_mask(size, radius):
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def gradient(size):
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        ratio = y / (size - 1)
        color = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * ratio) for i in range(3))
        draw.line([(0, y), (size, y)], fill=color)
    return img


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)

    base = gradient(SIZE).convert('RGBA')
    base.putalpha(rounded_mask(SIZE, radius=int(SIZE * 0.22)))

    # Wi-Fi 符号：三条同心圆弧 + 底部圆点，圆心在下方正中
    overlay = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = SIZE / 2, SIZE * 0.78
    for radius, width in ((SIZE * 0.52, 74), (SIZE * 0.36, 74), (SIZE * 0.20, 74)):
        box = [cx - radius, cy - radius, cx + radius, cy + radius]
        draw.arc(box, start=200, end=340, fill=WHITE, width=width)
    dot = SIZE * 0.055
    draw.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=WHITE)

    icon = Image.alpha_composite(base, overlay)

    png_path = ASSETS / 'icon.png'
    icon.resize((256, 256), Image.LANCZOS).save(png_path)

    ico_path = ASSETS / 'icon.ico'
    icon.save(ico_path, format='ICO',
              sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    print(f'已生成 {png_path}')
    print(f'已生成 {ico_path}')


if __name__ == '__main__':
    main()