
import pdb
from language_detector import YoloLangDetector, TextLangDetector
from format_utils import convert_to_images
from tqdm import tqdm
import pandas as pd


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate language detection model.")
    parser.add_argument("--model_path", type=str, default=None, help="Path to the language detection model.")
    parser.add_argument("--test_data", type=str, required=True, help="Path to the test data file.")
    parser.add_argument("--root_folder", type=str, default=None, help="Root folder for the test data files.")
    args = parser.parse_args()

    # Initialize the language detector
    if args.model_path is None:
        lang_detector = TextLangDetector(labels={0: "ar", 1: "en", 2: "ar-en"})
    else:
        lang_detector = YoloLangDetector(model_path=args.model_path, labels={0: "ar", 1: "en"})

    df = pd.read_csv(args.test_data, encoding='utf-8',sep='\t')
    df['full_path'] = df['store_path'].apply(lambda x: f"{args.root_folder}/{x}" if args.root_folder else x)
    results = lang_detector.evaluate(df['full_path'].tolist())
    pdb.set_trace()
    
    print("Evaluation Results:", results)