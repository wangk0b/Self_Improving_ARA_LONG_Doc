import random
from collections import Counter
from ultralytics import YOLO
from multiprocessing import Pool, cpu_count
from functools import partial

from format_utils import convert_to_images, read_file
from validation_schema import ValidationError

import numpy as np

import logging
logging.getLogger('ultralytics').setLevel(logging.ERROR)


class LangDetector():
    
    def __init__(self,labels,layout_segmenter=None):
        self.labels = labels
        self.layout_segmenter = layout_segmenter
        
        assert type(labels) is dict, "labels should be dict "         
    
    def sample_inputs(self,images,num_pages=15,perc=None):
        
        total_images = len(images)
        
        if ( num_pages > 0 ) and (not perc):
            _range = min(total_images,num_pages)
            return [images[i] for i in list(range(0, _range)) ], list(range(0, _range))
            
        num_samples = total_images * perc
        num_samples = int(num_samples) if num_samples >= total_images else int(total_images)
        
        indices = random.sample(range(0, total_images), num_samples)
        sample_img = [ np.array(images[i]) for i in indices ]
        
        return sample_img, indices
    
    def __call__(self,inputs):
        pass 
    
    
    def get_lang(self,inputs,perc=None):
        try:
            inputs, indc = self.sample_inputs(inputs,15,perc) 
            if self.layout_segmenter is not None:
                inputs = self.layout_segmenter.detect_layout(inputs)
            
            labels = []
            for inp in inputs:
                res = self.__call__(inp)
                labels.append(res)
            
            mapped_labels = [self.labels[i] for i in labels]

            # Count occurrences
            counts = Counter(mapped_labels)

            if len(counts.keys()) == 2:
                return 'ar-en'
            else:
                return list(counts.keys())[0]
            
            # final_lang = counts.most_common(1)[0][0]
            return final_lang 
        
        except Exception as e:
            logging.error(f"Error in get_lang: {e}")
            raise e
        
    def evaluate(self, file_paths: list[str], num_processes=None):
        """
        Evaluate the language detection model on a set of file paths using multiprocessing.
        Args:
            file_paths: List of file paths to evaluate.
            num_processes: Number of processes to use. If None, uses cpu_count().
        Returns:
            A dictionary with the evaluation results.
        """
        if num_processes is None:
            num_processes = cpu_count() - 5  # Reserve some CPU cores for other tasks
            
        # Use multiprocessing to process files in parallel

        with Pool(processes=num_processes) as pool:
            results = pool.map(self._evaluate_single_file, file_paths)

        # Aggregate results
        all_predictions = []
        for result in results:
            if result is not None:
                all_predictions.append(result)
        
        return {
            "file_predictions": dict(zip(file_paths, all_predictions)),
            "labels": self.labels,
            "total_files": len(file_paths),
            "processed_files": len(all_predictions)
        }
    
    def _evaluate_single_file(self, file_path: str):
        """
        Evaluate a single file for language detection.
        Args:
            file_path: Path to the file to evaluate.
        Returns:
            Language prediction result or None if error occurs.
        """
        
        if isinstance(self, TextLangDetector):
            content = read_file(file_path)
        else:
            content = convert_to_images(file_path)
            
        res = self.get_lang([content], perc=1.0)
        
        return res 

class TextLangDetector(LangDetector):

    def __init__(self,labels):
        super(TextLangDetector, self).__init__(labels)
        # Arabic Unicode ranges
        self.arabic_ranges = [
            (0x0600, 0x06FF),  # Arabic
            (0x0750, 0x077F),  # Arabic Supplement
            (0x08A0, 0x08FF),  # Arabic Extended-A
            (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
            (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        ]
        
        # English/Latin Unicode ranges
        self.english_ranges = [
            (0x0041, 0x005A),  # Basic Latin uppercase
            (0x0061, 0x007A),  # Basic Latin lowercase
            (0x00C0, 0x00FF),  # Latin-1 Supplement
            (0x0100, 0x017F),  # Latin Extended-A
            (0x0180, 0x024F),  # Latin Extended-B
        ]

    def __call__(self,inputs):
        '''
        Count the number of Arabic, English, and other characters in the text. 
        '''
        def is_in_ranges(ch, ranges):
            code = ord(ch)
            return any(start <= code <= end for start, end in ranges)
        
        arabic = english = other = 0
        for ch in inputs:
            if ch.isspace():
                continue
            if is_in_ranges(ch, self.arabic_ranges):
                arabic += 1
            elif is_in_ranges(ch, self.english_ranges):
                english += 1
            else:
                other += 1
        
        total = arabic + english + other
        if arabic > english:
            return 1
        elif english> arabic:
            return 0
        
        return 0.5
        
            
class YoloLangDetector(LangDetector):
    def __init__(self,labels,model_path,layout_segmenter):
        super(YoloLangDetector, self).__init__(labels,layout_segmenter)
        self.model = YOLO(model_path)
        
    def __call__(self,inputs):
        res = self.model(inputs)[0]
        return res.probs.top1