import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QMouseEvent

from gui.widgets.image_canvas import ImageCanvas
from utils.qt_cv_utils import cv2_to_qpixmap

class GeometryCanvas(ImageCanvas):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay_item = QGraphicsPixmapItem()
        self.scene.addItem(self.overlay_item)
        self.overlay_item.setZValue(1)
        
        self.center_pt = None
        self.min_pt = None
        self.max_pt = None
        self.cv_shape = None
        
        self.active_mode = None # "center", "min", "max"
        
    def set_image(self, pixmap: QPixmap, cv_shape=None):
        super().set_image(pixmap)
        self.cv_shape = cv_shape
        self.update_overlay()
        
    def update_overlay(self):
        if self.cv_shape is None:
            return
            
        overlay = np.zeros((*self.cv_shape[:2], 4), dtype=np.uint8)
        
        # Colors (R, G, B, A)
        colors = {
            "center": (0, 0, 255, 255), # Red
            "min": (0, 255, 0, 255),    # Green
            "max": (255, 0, 0, 255)     # Blue
        }
        
        # Draw lines from center
        if self.center_pt is not None:
            c = tuple(self.center_pt)
            cv2.circle(overlay, c, 5, colors["center"], -1)
            
            if self.min_pt is not None:
                m = tuple(self.min_pt)
                cv2.line(overlay, c, m, colors["min"], 2)
                cv2.circle(overlay, m, 5, colors["min"], -1)
                
            if self.max_pt is not None:
                mx = tuple(self.max_pt)
                cv2.line(overlay, c, mx, colors["max"], 2)
                cv2.circle(overlay, mx, 5, colors["max"], -1)
                
        pixmap = cv2_to_qpixmap(overlay)
        self.overlay_item.setPixmap(pixmap)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.active_mode:
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            
            if self.active_mode == "center":
                self.center_pt = [x, y]
            elif self.active_mode == "min":
                self.min_pt = [x, y]
            elif self.active_mode == "max":
                self.max_pt = [x, y]
                
            self.update_overlay()
            event.accept()
        else:
            super().mousePressEvent(event)
