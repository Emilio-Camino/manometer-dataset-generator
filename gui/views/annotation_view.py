import os
import cv2
import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QRadioButton, QButtonGroup, QLineEdit, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt, Signal

from gui.widgets.geometry_canvas import GeometryCanvas
from utils.qt_cv_utils import cv2_to_qpixmap

class AnnotationView(QWidget):
    annotation_done = Signal()
    
    def __init__(self, wm, parent=None):
        super().__init__(parent)
        self.wm = wm
        self.current_img_path = None
        
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel("Módulo 2: Geometría de Manómetro")
        font = self.lbl_title.font()
        font.setBold(True)
        self.lbl_title.setFont(font)
        layout.addWidget(self.lbl_title)
        
        tools_layout = QHBoxLayout()
        
        # Modes
        mode_layout = QVBoxLayout()
        self.btn_center = QRadioButton("Marcar Centro")
        self.btn_min = QRadioButton("Marcar Mínimo")
        self.btn_max = QRadioButton("Marcar Máximo")
        self.btn_center.setChecked(True)
        
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.btn_center)
        self.mode_group.addButton(self.btn_min)
        self.mode_group.addButton(self.btn_max)
        
        self.btn_center.toggled.connect(self._on_mode_changed)
        self.btn_min.toggled.connect(self._on_mode_changed)
        self.btn_max.toggled.connect(self._on_mode_changed)
        
        mode_layout.addWidget(self.btn_center)
        mode_layout.addWidget(self.btn_min)
        mode_layout.addWidget(self.btn_max)
        tools_layout.addLayout(mode_layout)
        
        # Values
        val_layout = QFormLayout()
        self.txt_val_min = QLineEdit("0")
        self.txt_val_max = QLineEdit("100")
        val_layout.addRow("Valor Mínimo:", self.txt_val_min)
        val_layout.addRow("Valor Máximo:", self.txt_val_max)
        tools_layout.addLayout(val_layout)
        
        self.btn_save = QPushButton("Guardar Anotaciones")
        self.btn_save.clicked.connect(self._on_save)
        tools_layout.addWidget(self.btn_save)
        
        layout.addLayout(tools_layout)
        
        self.canvas = GeometryCanvas()
        self.canvas.active_mode = "center"
        layout.addWidget(self.canvas)
        
    def load_image(self, img_path):
        self.current_img_path = img_path
        filename = os.path.basename(img_path)
        self.lbl_title.setText(f"Módulo 2: Geometría de Manómetro - {filename}")
        
        if os.path.exists(img_path):
            cv_img = cv2.imread(img_path)
            pixmap = cv2_to_qpixmap(cv_img)
            self.canvas.set_image(pixmap, cv_shape=cv_img.shape)
            
        # Load existing local config
        geo = self.wm.load_local_annotation(img_path)
        if geo:
            if "center" in geo: self.canvas.center_pt = geo["center"]
            if "min_pt" in geo: self.canvas.min_pt = geo["min_pt"]
            if "max_pt" in geo: self.canvas.max_pt = geo["max_pt"]
            if "min_val" in geo: self.txt_val_min.setText(str(geo["min_val"]))
            if "max_val" in geo: self.txt_val_max.setText(str(geo["max_val"]))
            self.canvas.update_overlay()
        else:
            self.canvas.center_pt = None
            self.canvas.min_pt = None
            self.canvas.max_pt = None
            self.canvas.update_overlay()
            
    def _on_mode_changed(self):
        if self.btn_center.isChecked(): self.canvas.active_mode = "center"
        elif self.btn_min.isChecked(): self.canvas.active_mode = "min"
        elif self.btn_max.isChecked(): self.canvas.active_mode = "max"
        
    def _get_angle(self, center, point):
        dx = point[0] - center[0]
        dy = center[1] - point[1] # Invert Y for image coords
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad)
        
    def _on_save(self):
        if self.current_img_path is None: return
        if self.canvas.center_pt is None or self.canvas.min_pt is None or self.canvas.max_pt is None:
            QMessageBox.warning(self, "Faltan datos", "Debes marcar el Centro, Mínimo y Máximo.")
            return
            
        try:
            min_val = float(self.txt_val_min.text())
            max_val = float(self.txt_val_max.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Los valores mínimo y máximo deben ser números.")
            return
            
        c = self.canvas.center_pt
        angle_min = self._get_angle(c, self.canvas.min_pt)
        angle_max = self._get_angle(c, self.canvas.max_pt)
        
        filename = os.path.basename(self.current_img_path)
        data = {
            "path": self.current_img_path,
            "center": c,
            "min_pt": self.canvas.min_pt,
            "max_pt": self.canvas.max_pt,
            "min_val": min_val,
            "max_val": max_val,
            "angle_min": angle_min,
            "angle_max": angle_max
        }
        self.wm.save_local_annotation(self.current_img_path, data)
        
        QMessageBox.information(self, "Éxito", "Anotaciones guardadas correctamente.")
        self.annotation_done.emit()
