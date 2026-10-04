# 폴더를 순회하며 텍스트 파일 추출

# 폴더 경로 설정
text_dir = '/content/drive/MyDrive/ShareforMe/oa_comm_txt.PMC000xxxxxx.baseline.2025-06-17/PMC000xxxxxx'

import os

def extract_txt(file_path):
    # 다양한 인코딩 대응
    try_encodings = ['utf-8', 'latin1', 'cp1252']

    for encoding in try_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read()
            break  # 성공적으로 읽었으면 루프 탈출
        except UnicodeDecodeError:
            continue
    else:
        print(f"[경고] {filename} 파일을 열 수 없습니다. (인코딩 문제)")
        text =''
    return text

for filename in os.listdir(text_dir):
    if not filename.endswith(".txt"):
        continue
    file_path = os.path.join(text_dir, filename)
    file_text = extract_txt(file_path)
    
