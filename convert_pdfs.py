import pymupdf4llm
import pymupdf
import os
import json
import re
from pathlib import Path

# PDF文件列表及其对应的政府归属
pdf_files = {
    "Americas-AI-Action-Plan.pdf": "特朗普政府",
    "NIST.AI.100-1.pdf": "拜登政府",
    "2025-05908.pdf": "特朗普政府",
    "2023-24283.pdf": "拜登政府",
    "2025-02345.pdf": "特朗普政府",
    "2025-02172.pdf": "特朗普政府",
}

def convert_pdf_to_markdown(pdf_path):
    """使用pymupdf4llm将PDF转换为markdown"""
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
        return md_text
    except Exception as e:
        print(f"Error converting {pdf_path}: {e}")
        return None

def remove_duplicates(text):
    """去除重复的段落和行"""
    lines = text.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique_lines.append(line)
        elif not stripped:  # 保留空行用于段落分隔
            unique_lines.append(line)
    return '\n'.join(unique_lines)

def extract_metadata_from_filename(filename):
    """从文件名提取元数据"""
    name = Path(filename).stem
    return name

# 主处理流程
output_dir = Path("converted_texts")
output_dir.mkdir(exist_ok=True)

results = {}
for pdf_file, government in pdf_files.items():
    pdf_path = Path(pdf_file)
    if pdf_path.exists():
        print(f"Converting: {pdf_file}")
        md_text = convert_pdf_to_markdown(pdf_path)
        if md_text:
            # 去除重复
            md_text = remove_duplicates(md_text)
            # 保存markdown
            output_file = output_dir / f"{pdf_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_text)
            results[pdf_file] = {
                "government": government,
                "output_file": str(output_file),
                "text_length": len(md_text)
            }
            print(f"  Saved to: {output_file} ({len(md_text)} chars)")
    else:
        print(f"File not found: {pdf_file}")

# 保存转换结果元数据
with open(output_dir / "conversion_metadata.json", 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nConversion complete. {len(results)} files processed.")
