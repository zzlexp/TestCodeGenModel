import os
import json
import csv
from collections import defaultdict

def process_raw_files():
    raw_dir = os.path.join(os.path.dirname(__file__), 'numpy_apis/raw')
    output_csv = os.path.join(os.path.dirname(__file__), 'numpy_apis/merged_data.csv')
    
    seen = defaultdict(set)
    unique_data = []

    for filename in os.listdir(raw_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(raw_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    for entry in data:
                        for api_name, api_info in entry.items():
                            # 使用API名称+描述作为唯一标识
                            identifier = f"{api_name}_{api_info['description'][:50]}"
                            if identifier not in seen[filename]:
                                unique_data.append({
                                    'api_name': api_name,
                                    'description': api_info['description'],
                                    'parameters': str(api_info.get('parameters', [])),
                                    'examples': '\n'.join(api_info.get('examples', []))
                                })
                                seen[filename].add(identifier)
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")

    print(len(unique_data))

    # 写入CSV文件
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['api_name', 'description', 'parameters', 'examples']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_data)

if __name__ == '__main__':
    process_raw_files()
    print("数据处理完成，结果已保存到 numpy_apis/merged_data.csv")