import os
import cv2
import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QRadioButton, QButtonGroup, QMessageBox)
from PySide6.QtCore import Qt, Signal

from gui.widgets.geometry_canvas import GeometryCanvas
from utils.qt_cv_utils import cv2_to_qpixmap

class NeedleAnnotationView(QWidget):
    annotation_done = Signal()
    
    def __init__(self, wm, parent=None):
        super().__init__(parent)
        self.wm = wm
        self.current_img_path = None
        
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel("Módulo 4: Anotación de Aguja")
        font = self.lbl_title.font()
        font.setBold(True)
        self.lbl_title.setFont(font)
        layout.addWidget(self.lbl_title)
        
        tools_layout = QHBoxLayout()
        
        # Modes
        mode_layout = QVBoxLayout()
        self.btn_pivot = QRadioButton("Marcar Pivote (Centro de rotación)")
        self.btn_tip = QRadioButton("Marcar Punta (Obligatorio)")
        self.btn_pivot.setChecked(True)
        
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.btn_pivot)
        self.mode_group.addButton(self.btn_tip)
        
        self.btn_pivot.toggled.connect(self._on_mode_changed)
        self.btn_tip.toggled.connect(self._on_mode_changed)
        
        mode_layout.addWidget(self.btn_pivot)
        mode_layout.addWidget(self.btn_tip)
        tools_layout.addLayout(mode_layout)
        
        self.btn_save = QPushButton("Guardar Pivote y Punta")
        self.btn_save.clicked.connect(self._on_save)
        tools_layout.addWidget(self.btn_save)
        
        layout.addLayout(tools_layout)
        
        self.canvas = GeometryCanvas()
        self.canvas.active_mode = "center" # Usamos 'center' de GeometryCanvas para el pivote
        layout.addWidget(self.canvas)
        
    def load_image(self, img_path):
        self.current_img_path = img_path
        filename = os.path.basename(img_path)
        self.lbl_title.setText(f"Módulo 4: Anotación de Aguja - {filename}")
        
        if os.path.exists(img_path):
            cv_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if cv_img is None:
                QMessageBox.warning(self, "Error", "No se pudo cargar la imagen")
                return
                
            # Si tiene transparencia, aplicamos un fondo gris oscuro
            import numpy as np
            if cv_img.shape[2] == 4:
                b, g, r, a = cv2.split(cv_img)
                bg = np.full((cv_img.shape[0], cv_img.shape[1], 3), 50, dtype=np.uint8)
                mask = a / 255.0
                fg = cv2.merge((b, g, r))
                cv_img = (fg * mask[:, :, np.newaxis] + bg * (1 - mask[:, :, np.newaxis])).astype(np.uint8)
                
            pixmap = cv2_to_qpixmap(cv_img)
            self.canvas.set_image(pixmap, cv_shape=cv_img.shape)
            
        # Load existing local config
        info = self.wm.load_local_annotation(img_path)
        if info:
            if "local_pivot" in info:
                self.canvas.center_pt = info["local_pivot"]
            if "local_tip" in info:
                self.canvas.min_pt = info["local_tip"]
            self.canvas.update_overlay()
        else:
            self.canvas.center_pt = None
            self.canvas.min_pt = None
            self.canvas.update_overlay()
            
    def _on_mode_changed(self):
        if self.btn_pivot.isChecked(): 
            self.canvas.active_mode = "center" # Mapeado a pivote
        elif self.btn_tip.isChecked(): 
            self.canvas.active_mode = "min"    # Mapeado a punta
        
    def _get_angle(self, center, point):
        dx = point[0] - center[0]
        dy = center[1] - point[1]
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad)
        
    def _on_save(self):
        if self.current_img_path is None: return
        if self.canvas.center_pt is None or self.canvas.min_pt is None:
            QMessageBox.warning(self, "Faltan datos", "Debes marcar el Pivote y la Punta de la aguja.")
            return
            
        pivot = self.canvas.center_pt
        
        if self.canvas.min_pt is not None:
            original_angle = self._get_angle(pivot, self.canvas.min_pt)
            tip = self.canvas.min_pt
        else:
            original_angle = 0.0
            tip = None
            
        filename = os.path.basename(self.current_img_path)
        data = {
            "path": self.current_img_path,
            "local_pivot": pivot,
            "local_tip": tip,
            "original_angle": original_angle
        }
        
        self.wm.save_local_annotation(self.current_img_path, data)
        
        QMessageBox.information(self, "Éxito", "Pivote guardado correctamente.")
        self.annotation_done.emit()
