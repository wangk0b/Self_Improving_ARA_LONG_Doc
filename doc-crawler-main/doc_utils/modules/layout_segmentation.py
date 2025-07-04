import numpy as np
from PIL import Image
from ultralytics import YOLO

import logging
logging.getLogger('ultralytics').setLevel(logging.ERROR)

class LayoutSegmentor():
    def __init__(self, model_path: str,device: str = 'cpu'):
        """
        Initialize the LayoutDetector with a YOLO model.
        
        Args:
            model_path (str): Path to the YOLO model file.
        """
        self.device = device
        self.model = YOLO(model_path)
        self.cols = {'List-item','Footnote','Page-header','Section-header','Text','Title','Table','Caption'}
        
    def __call__(self, *args, **kwds):
        pass
        
    def get_array_images(self, image, yolo_obj,save_images: bool = False):
        """
        Extracts array images from the YOLO object.
        
        Args:
            image: Input image from which to extract array images.
            yolo_obj: YOLO object containing detection results.
        
        Returns:
            List of array images.
        """
        if not isinstance(image, Image.Image):
            image = Image.open(image)
            
        obj_num = 0
        images = []
        for layout_obj in yolo_obj.boxes:
            cls_num = int(layout_obj.cls[0])
            cls = self.model.names[cls_num]
            if cls in self.cols:
                x0, y0, x1, y1 = [float(x) for x in layout_obj.xyxy[0]]
                cropped_img = image.crop((x0, y0, x1, y1))
                
                # Save the image
                if save_images:
                    cropped_img.save(f'test_result/page_1_{obj_num}_{cls}.png')

                # Convert to NumPy array
                img_array = np.array(cropped_img)
                images.append(img_array)
        
        return images
    
    def detect_layout(self, images):
        """
        Detect layout in the given image.
        
        Args:
            image: Input image for layout detection.
        
        Returns:
            List of detected layout objects.
        """
        results = []
        for img in images:
            result = self.model(img, device=self.device, verbose=False)[0]
            segmented_image = self.get_array_images(img, result, save_images=False)
            results.append(segmented_image)
        return results
    
    def __call__(self, image):
        """
        Detect layout in the given image.
        
        Args:
            image: Input image for layout detection.
        
        Returns:
            List of detected layout objects.
        """
        results = self.model(image, device=self.device, verbose=False)[0]
        
        return results
    
