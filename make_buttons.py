"""把按钮 JPG 去白底，生成带透明通道的 PNG。

只删除与图像边框相连的白色背景（连通域），按钮内部（含浅粉、白字、高光）
一律保留实心，避免之前用亮度阈值把红色通道恒为 255 的粉色内容误删。
"""
import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(ROOT, "assets", "UI")

NAMES = [
    "开始游戏按钮", "游戏规则按钮", "返回按钮", "重新开始按钮",
    "下一关按钮", "好的按钮", "返回主菜单按钮",
]

WHITE_THRESH = 240  # min(r,g,b) >= 240 视为“白”（背景）


def make_alpha(rgb: np.ndarray) -> np.ndarray:
    """返回 0(背景)/255(内容) 的 alpha 掩码，0/255 二值。"""
    h, w = rgb.shape[:2]
    mn = rgb.min(axis=2)
    white = (mn >= WHITE_THRESH).astype(np.uint8)

    # 连通域：背景 = 与边框相连的白色连通块
    num, labels = cv2.connectedComponents(white, connectivity=4)

    border = set()
    border.update(labels[0, :].tolist())
    border.update(labels[-1, :].tolist())
    border.update(labels[:, 0].tolist())
    border.update(labels[:, -1].tolist())
    border.discard(0)

    bg = np.isin(labels, list(border)).astype(np.uint8)

    # 背景向外膨胀 1px，吃掉白→粉过渡的浅色边缘
    bg = cv2.dilate(bg, np.ones((3, 3), np.uint8), iterations=1)

    return np.where(bg == 0, 255, 0).astype(np.uint8)


def main():
    for name in NAMES:
        src = os.path.join(UI, name + ".jpg")
        dst = os.path.join(UI, name + ".png")

        rgb = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_COLOR)  # BGR
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)

        alpha = make_alpha(rgb)
        rgba = np.dstack([rgb, alpha])

        Image.fromarray(rgba, "RGBA").save(dst)

        transparent = (alpha < 10).mean()
        print(f"{name}: 透明像素占比 {transparent:.1%}  -> {os.path.basename(dst)}")


if __name__ == "__main__":
    main()
