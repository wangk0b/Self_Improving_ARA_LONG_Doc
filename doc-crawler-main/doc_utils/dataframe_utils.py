import pandas as pd

def save_to_tsv(rows, output_path):
    df = pd.DataFrame(columns=[
        "language", "category", "sub_category", "format",
        "file_size", "orientation", "number_of_pages",
        "source_url", "downloadable_link", "download_time", "store_path"
    ],data=rows)
    df.to_csv(output_path, sep='\t', index=False, encoding='utf-8')
    return df

def summarize_metadata(df):
    print("Total number of files:", len(df))
    print("\n📊 Summary Breakdown:")
    summary = {}
    for col in ['language', 'category', 'sub_category', 'format', 'orientation']:
        if col in df.columns and df[col].dtype == 'object':
            counts = df[col].value_counts()
            for value, count in counts.items():
                summary[value] = {
                'count': count,
                'percentage': (count / len(df)) * 100
            } 
    
    for cat, data in summary.items():
        print(f"{cat}: {data['count']} files ({data['percentage']:.2f}%)")