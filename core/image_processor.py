import cv2
import numpy as np

class ImageProcessor:
    @staticmethod
    def create_empty_mask(shape):
        if len(shape) == 3:
            return np.zeros(shape[:2], dtype=np.uint8)
        return np.zeros(shape, dtype=np.uint8)

    @staticmethod
    def draw_on_mask(mask, pt1, pt2, radius, color, thickness=-1):
        cv2.line(mask, pt1, pt2, color, thickness=radius)
        cv2.circle(mask, pt2, radius // 2, color, thickness=-1)
        
    @staticmethod
    def apply_grabcut(image, mask):
        """Refines the drawn mask using GrabCut."""
        # Check if mask has any drawings
        coords = cv2.findNonZero(mask)
        if coords is None:
            return mask
            
        x, y, w, h = cv2.boundingRect(coords)
        
        # Add margin to bounding box
        margin = 20
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(image.shape[1] - x, w + margin * 2)
        h = min(image.shape[0] - y, h + margin * 2)
        
        rect = (x, y, w, h)
        
        # Initialize GrabCut mask
        gc_mask = np.zeros(image.shape[:2], np.uint8)
        gc_mask.fill(cv2.GC_BGD) # Default to definite background
        gc_mask[y:y+h, x:x+w] = cv2.GC_PR_BGD # Inside rect is probable background
        
        # Set user drawn mask as definite foreground
        gc_mask[mask > 0] = cv2.GC_FGD
        
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        # Run GrabCut
        cv2.grabCut(image, gc_mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_MASK)
        
        # Extract refined mask (GC_FGD and GC_PR_FGD)
        refined_mask = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype('uint8')
        return refined_mask
        
    @staticmethod
    def extract_needle(image, mask):
        coords = cv2.findNonZero(mask)
        if coords is None:
            return None, None
            
        x, y, w, h = cv2.boundingRect(coords)
        needle_crop = image[y:y+h, x:x+w]
        mask_crop = mask[y:y+h, x:x+w]
        
        if len(needle_crop.shape) == 3 and needle_crop.shape[2] == 3:
            b, g, r = cv2.split(needle_crop)
            rgba = [b, g, r, mask_crop]
            return cv2.merge(rgba), (x, y) # Return crop and its top-left position
        elif len(needle_crop.shape) == 3 and needle_crop.shape[2] == 4:
            b, g, r, a = cv2.split(needle_crop)
            return cv2.merge([b, g, r, mask_crop]), (x, y)
        return None, None
        
    @staticmethod
    def inpaint_background_opencv(image, mask, method=cv2.INPAINT_TELEA, dilate_iter=1):
        if dilate_iter > 0:
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=dilate_iter)
        return cv2.inpaint(image, mask, 3, method)
        
    @staticmethod
    def inpaint_background_lama(image, mask):
        try:
            from simple_lama_inpainting import SimpleLama
            from PIL import Image
            
            lama = SimpleLama()
            
            # Convert OpenCV to PIL
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(image_rgb)
            mask_pil = Image.fromarray(mask).convert('L')
            
            # Inpaint
            result_pil = lama(img_pil, mask_pil)
            
            # Convert PIL back to OpenCV
            result_cv = np.array(result_pil)
            result_cv = cv2.cvtColor(result_cv, cv2.COLOR_RGB2BGR)
            return result_cv
        except ImportError:
            print("simple-lama-inpainting no está instalado.")
            return None
            
    @staticmethod
    def rotate_needle(needle_img, angle, pivot):
        if needle_img is None:
            return None
            
        h, w = needle_img.shape[:2]
        M = cv2.getRotationMatrix2D(pivot, angle, 1.0)
        
        # Calculate new bounding box to prevent cropping
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        
        # Adjust matrix for translation
        M[0, 2] += (nW / 2) - pivot[0]
        M[1, 2] += (nH / 2) - pivot[1]
        
        rotated = cv2.warpAffine(needle_img, M, (nW, nH), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
        
        # Return rotated image and the offset of the new center relative to pivot
        offset_x = (nW / 2) - pivot[0]
        offset_y = (nH / 2) - pivot[1]
        
        return rotated, (offset_x, offset_y)
        
    @staticmethod
    def overlay_image(background, overlay, position):
        if overlay is None or background is None:
            return background
            
        x, y = int(position[0]), int(position[1])
        h, w = overlay.shape[:2]
        
        bh, bw = background.shape[:2]
        
        x1, x2 = max(0, x), min(bw, x + w)
        y1, y2 = max(0, y), min(bh, y + h)
        
        if x1 >= x2 or y1 >= y2:
            return background
            
        ox1, ox2 = x1 - x, x2 - x
        oy1, oy2 = y1 - y, y2 - y
        
        overlay_crop = overlay[oy1:oy2, ox1:ox2]
        bg_crop = background[y1:y2, x1:x2]
        
        if overlay_crop.shape[2] == 4:
            alpha = overlay_crop[:, :, 3] / 255.0
            for c in range(3):
                bg_crop[:, :, c] = (alpha * overlay_crop[:, :, c] + (1 - alpha) * bg_crop[:, :, c])
                
        background[y1:y2, x1:x2] = bg_crop
        return background
