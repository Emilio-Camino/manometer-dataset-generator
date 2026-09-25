import cv2
from PySide6.QtGui import QImage, QPixmap
import numpy as np

def cv2_to_qpixmap(cv_img):
    """Convert an OpenCV image (numpy array) to QPixmap."""
    if cv_img is None:
        return QPixmap()
        
    if len(cv_img.shape) == 2:
        # Grayscale
        h, w = cv_img.shape
        bytes_per_line = w
        q_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
    elif len(cv_img.shape) == 3:
        if cv_img.shape[2] == 3:
            # BGR
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            # Qt uses RGB, OpenCV uses BGR
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # We must copy because rgb_img data goes out of scope
            q_img = q_img.copy()
        elif cv_img.shape[2] == 4:
            # BGRA
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            rgba_img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
            q_img = QImage(rgba_img.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
            q_img = q_img.copy()
        else:
            return QPixmap()
    else:
        return QPixmap()
        
    return QPixmap.fromImage(q_img)
