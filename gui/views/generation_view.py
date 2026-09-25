import os
import cv2
import json
import random
import math
import concurrent.futures
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QMessageBox, QFormLayout, 
                               QProgressBar, QFileDialog)
from PySide6.QtCore import Qt

from core.image_processor import ImageProcessor

class GenerationView(QWidget):
    def __init__(self, wm, parent=None):
        super().__init__(parent)
        self.wm = wm
        
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel("Módulo 5: Generación Combinatoria de Dataset")
        font = self.lbl_title.font()
        font.setBold(True)
        self.lbl_title.setFont(font)
        layout.addWidget(self.lbl_title)
        
        # Generation inputs
        gen_layout = QFormLayout()
        
        self.txt_count = QLineEdit("70")
        gen_layout.addRow("Imágenes por combinación:", self.txt_count)
        
        self.btn_select_out = QPushButton("Seleccionar Directorio de Salida")
        self.btn_select_out.clicked.connect(self._on_select_out)
        gen_layout.addRow("", self.btn_select_out)
        
        self.lbl_out = QLabel("Directorio de Salida: No seleccionado")
        gen_layout.addRow("", self.lbl_out)
        
        self.btn_generate = QPushButton("Generar Dataset Combinatorio")
        self.btn_generate.clicked.connect(self._on_generate)
        gen_layout.addRow("", self.btn_generate)
        
        layout.addLayout(gen_layout)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        
        self.output_dir = None
        
        last_out = self.wm.get_setting("last_output_dir")
        if last_out and os.path.exists(last_out):
            self.output_dir = last_out
            self.lbl_out.setText(f"Directorio de Salida: {self.output_dir}")
            
    def _on_select_out(self):
        last_dir = self.wm.get_setting("last_output_dir", "")
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Salida", last_dir)
        if folder:
            self.output_dir = folder
            self.wm.set_setting("last_output_dir", folder)
            self.lbl_out.setText(f"Directorio de Salida: {self.output_dir}")
            
    @staticmethod
    def _process_single_frame(task):
        if len(task) == 9:
            d_img, n_img, dial, needle, i, samples_per_combo, img_out_dir, lbl_out_dir, job_seed = task
        else:
            d_img, n_img, dial, needle, i, samples_per_combo, img_out_dir, lbl_out_dir = task
            job_seed = "fixed"

        
        d_name = os.path.basename(dial["path"])
        n_name = os.path.basename(needle["path"])
        
        min_v = dial["min_val"]
        max_v = dial["max_val"]
        cx, cy = dial["center"]
        
        seed_str = f"{d_name}_{n_name}_{job_seed}"
        rng = random.Random(seed_str)
        
        # Pre-calculate all values for this combo and shuffle them
        values = []
        if samples_per_combo > 1:
            bin_size = (max_v - min_v) / samples_per_combo
            for j in range(samples_per_combo):
                bin_start = min_v + j * bin_size
                bin_end = bin_start + bin_size
                v = rng.uniform(bin_start, bin_end)
                values.append(max(min_v, min(max_v, v)))
        else:
            v = rng.uniform(min_v, max_v)
            values.append(max(min_v, min(max_v, v)))
            
        rng.shuffle(values)
        val = round(values[i], 3)
        
        # 1. Escala Dinámica de la Aguja
        needle_img = n_img.copy()
        local_pivot = list(needle["local_pivot"])
        local_tip = needle.get("local_tip")
        min_pt = dial.get("min_pt")
        
        if local_tip and min_pt:
            dial_radius = math.dist(dial["center"], min_pt)
            needle_length = math.dist(local_pivot, local_tip)
            
            if needle_length > 0:
                scale_factor = dial_radius / needle_length
                if 0.2 < scale_factor < 5.0:
                    new_w = int(needle_img.shape[1] * scale_factor)
                    new_h = int(needle_img.shape[0] * scale_factor)
                    needle_img = cv2.resize(needle_img, (new_w, new_h))
                    local_pivot = [int(p * scale_factor) for p in local_pivot]
        
        min_a = dial["angle_min"]
        max_a = dial["angle_max"]
        
        if max_v == min_v:
            pct = 0
        else:
            pct = (val - min_v) / (max_v - min_v)
            
        target_angle = min_a + (max_a - min_a) * pct
        original_angle = needle["original_angle"]
        
        # 2. Invertir rotación
        delta_angle = -(target_angle - original_angle)
        
        rotated_needle, new_offset = ImageProcessor.rotate_needle(needle_img, delta_angle, local_pivot)
        
        px = cx - new_offset[0] - local_pivot[0]
        py = cy - new_offset[1] - local_pivot[1]
        
        frame = d_img.copy()
        frame = ImageProcessor.overlay_image(frame, rotated_needle, (px, py))
        
        d_base = os.path.splitext(d_name)[0]
        n_base = os.path.splitext(n_name)[0]
        filename = f"gen_{d_base}_{n_base}_{i:03d}.png"
        filepath = os.path.join(img_out_dir, filename)
        cv2.imwrite(filepath, frame)
        
        # Generate JSON label
        json_data = {
            "image_filename": filename,
            "dial_source": d_name,
            "needle_source": n_name,
            "value": val,
            "angle": target_angle,
            "center": [cx, cy]
        }
        json_filename = f"gen_{d_base}_{n_base}_{i:03d}.json"
        json_filepath = os.path.join(lbl_out_dir, json_filename)
        with open(json_filepath, 'w', encoding='utf-8') as jf:
            json.dump(json_data, jf, indent=4)
            
        return True

    def _on_generate(self):
        if not self.output_dir:
            QMessageBox.warning(self, "Error", "Seleccione un directorio de salida.")
            return
            
        try:
            samples_per_combo = int(self.txt_count.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Cantidad inválida.")
            return
            
        if samples_per_combo < 1: return
        
        dial_dir = self.wm.get_setting("last_dial_dir", "")
        needle_dir = self.wm.get_setting("last_needle_dir", "")
        
        dials_data = self.wm.get_all_annotations_in_folder(dial_dir)
        needles_data = self.wm.get_all_annotations_in_folder(needle_dir)
        
        valid_dials = [v for k, v in dials_data.items() if os.path.exists(v.get("path", ""))]
        valid_needles = [v for k, v in needles_data.items() if os.path.exists(v.get("path", ""))]
        
        if not valid_dials or not valid_needles:
            QMessageBox.warning(self, "Faltan datos", 
                f"Diales válidos: {len(valid_dials)}\nAgujas válidas: {len(valid_needles)}\n"
                "Asegúrate de anotar al menos un dial y una aguja."
            )
            return
            
        total_images = len(valid_dials) * len(valid_needles) * samples_per_combo
        
        msg = f"Se generarán {total_images} imágenes combinando {len(valid_dials)} diales y {len(valid_needles)} agujas.\n¿Desea continuar?"
        resp = QMessageBox.question(self, "Confirmar Generación", msg)
        if resp != QMessageBox.StandardButton.Yes:
            return
            
        img_out_dir = os.path.join(self.output_dir, "images")
        lbl_out_dir = os.path.join(self.output_dir, "labels")
        os.makedirs(img_out_dir, exist_ok=True)
        os.makedirs(lbl_out_dir, exist_ok=True)
        
        self.progress.setVisible(True)
        self.progress.setMaximum(total_images)
        self.progress.setValue(0)
        
        generated_count = 0
        
        # Pre-load images to memory so threads don't bottleneck on disk I/O
        dial_images = {}
        for dial in valid_dials:
            img = cv2.imread(dial["path"])
            if img is not None:
                dial_images[dial["path"]] = img
                
        needle_images = {}
        for needle in valid_needles:
            img = cv2.imread(needle["path"], cv2.IMREAD_UNCHANGED)
            if img is not None:
                needle_images[needle["path"]] = img
                
        # Build task list
        job_seed = random.randint(0, 999999999)
        tasks = []
        for dial in valid_dials:
            d_img = dial_images.get(dial["path"])
            if d_img is None: continue
            
            for needle in valid_needles:
                n_img = needle_images.get(needle["path"])
                if n_img is None: continue
                
                for i in range(samples_per_combo):
                    tasks.append((d_img, n_img, dial, needle, i, samples_per_combo, img_out_dir, lbl_out_dir, job_seed))
                    
        total_images = len(tasks)
        if total_images == 0:
            QMessageBox.warning(self, "Error", "No se pudieron cargar las imágenes.")
            self.progress.setVisible(False)
            self.lbl_status.setText("")
            return
            
        self.progress.setMaximum(total_images)
        self.lbl_status.setText(f"Generando {total_images} imágenes en paralelo...")
        import PySide6.QtWidgets
        PySide6.QtWidgets.QApplication.processEvents()
        
        generated_count = 0
        
        # Execute in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._process_single_frame, t) for t in tasks]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                    generated_count += 1
                    self.progress.setValue(generated_count)
                    
                    # Update status slightly less frequently to avoid UI overhead
                    if generated_count % 10 == 0 or generated_count == total_images:
                        self.lbl_status.setText(f"Generando: {generated_count} / {total_images}")
                        PySide6.QtWidgets.QApplication.processEvents()
                except Exception as e:
                    print(f"Error generando imagen: {e}")
                        
        QMessageBox.information(self, "Completado", f"Generadas {generated_count} imágenes exitosamente.")
        self.progress.setVisible(False)
        self.lbl_status.setText("Generación finalizada.")
