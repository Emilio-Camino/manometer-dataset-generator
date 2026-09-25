import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter

from gui.widgets.image_canvas import ImageCanvas
from utils.qt_cv_utils import cv2_to_qpixmap

class MaskCanvas(ImageCanvas):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay_item = QGraphicsPixmapItem()
        self.scene.addItem(self.overlay_item)
        self.overlay_item.setZValue(1)
        self.overlay_item.setOpacity(0.6)
        
        self.mask = None
        self.drawing = False
        self.last_point = None
        self.brush_size = 15
        
        # Modes: "draw", "erase", "pivot", "tip"
        self.active_mode = "draw" 
        
        self.pivot_pt = None
        self.tip_pt = None
        
    def set_image(self, pixmap: QPixmap, cv_shape=None):
        super().set_image(pixmap)
        if cv_shape is not None:
            self.mask = np.zeros(cv_shape[:2], dtype=np.uint8)
            self.update_overlay()
            
    def set_mask(self, mask):
        self.mask = mask.copy()
        self.update_overlay()
        
    def update_overlay(self):
        if self.mask is None:
            return
            
        overlay = np.zeros((*self.mask.shape, 4), dtype=np.uint8)
        
        # Draw mask as red
        overlay[self.mask > 0] = [255, 0, 0, 255] 
        
        # Draw pivot (green) and tip (blue)
        if self.pivot_pt:
            cv2.circle(overlay, tuple(self.pivot_pt), 6, (0, 255, 0, 255), -1)
        if self.tip_pt:
            cv2.circle(overlay, tuple(self.tip_pt), 6, (255, 255, 0, 255), -1)
            
        pixmap = cv2_to_qpixmap(overlay)
        self.overlay_item.setPixmap(pixmap)
        
    def _draw_line(self, pt1, pt2):
        if self.mask is None:
            return
            
        color = 255 if self.active_mode == "draw" else 0
        cv2.line(self.mask, pt1, pt2, color, self.brush_size)
        cv2.circle(self.mask, pt2, self.brush_size // 2, color, -1)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            
            if self.active_mode in ["draw", "erase"]:
                self.drawing = True
                self.last_point = (x, y)
                self._draw_line((x, y), (x, y))
            elif self.active_mode == "pivot":
                self.pivot_pt = [x, y]
            elif self.active_mode == "tip":
                self.tip_pt = [x, y]
                
            self.update_overlay()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing and self.active_mode in ["draw", "erase"]:
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            self._draw_line(self.last_point, (x, y))
            self.last_point = (x, y)
            self.update_overlay()
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
