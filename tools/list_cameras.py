from typing import List

from cv2 import VideoCapture
from loguru import logger

for i in range(0, 10):
    try:
        v: VideoCapture = VideoCapture(index=i)
        if v.isOpened():
            logger.info(f"Found a camera! Camera {{ id: {i} }}")
    except Exception:
        pass