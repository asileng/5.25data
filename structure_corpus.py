import json
import re
import os
from pathlib import Path

# 文件配置
pdf_files = {
    "2025-02172.md": {"name": "Executive Order 14179", "government": "特朗普政府", "full_name": "Removing Barriers to American Leadership in Artificial Intelligence"},
    "2025-05908.md": {"name": "Executive Order 14255", "government": "特朗普政府", "full_name": "Establishing the United States Investment Accelerator"},
    "2025-02345.md": {"name": "Executive Order 14192", "government": "特朗普政府", "full_name": "Unleashing Prosperity Through Deregulation"},
    "2023-24283.md": {"name": "Executive Order 14110", "government": "拜登政府", "full_name": "Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence"},
    "NIST.AI.100-1.md": {"name": "NIST AI 100-1", "government": "拜登政府", "full_name": "Artificial Intelligence Risk Management Framework"},
    "Americas-AI-Action-Plan.md": {"name": "America's AI Action Plan", "government": "特朗普政府", "full_name": "Winning the Race: America's AI Action Plan"},
}

def is_garbage_line(line):
    """判断是否为垃圾行（页码、页眉、页脚等）"""
    stripped = line.strip()
    if not stripped:
        return True
    # 纯数字页码
    if re.match(r'^\d{1,4}$', stripped):
        return True
    # 页眉格式：Federal Register / Vol. XX
    if re.match(r'^\*{0,2}Federal Register\*{0,2}', stripped):
        return True
    # 页码格式：**14701** 等
    if re.match(r'^\*{1,2}\d{4,5}\*{1,2}$', stripped):
        return True
    # 页脚格式：[FR Doc. ...]
    if re.match(r'^\[FR Doc\.', stripped):
        return True
    # Billing code
    if 'Billing code' in stripped:
        return True
    # Vol. XX, No. XX
    if re.match(r'^Vol\.\s+\d+', stripped):
        return True
    # Friday/Thursday/Monday等日期行
    if re.match(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),', stripped):
        return True
    # 图片占位符
    if 'intentionally omitted' in stripped:
        return True
    # 空白图片行
    if stripped.startswith('**==>') and 'picture' in stripped:
        return True
    # 纯标点或特殊字符
    if re.match(r'^[\s\*\-\_\.\,\;\:]+$', stripped):
        return True
    # 只有单个字母或数字
    if re.match(r'^[a-zA-Z]$', stripped):
        return True
    # 短横线页码
    if re.match(r'^[-–—]\s*\d+\s*[-–—]$', stripped):
        return True
    return False

def clean_line(line):
    """清理单行文本"""
    # 去除markdown格式标记
    line = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', line)  # 去除粗体/斜体标记
    line = re.sub(r'^#+\s*', '', line)  # 去除标题标记
    line = re.sub(r'^>\s*', '', line)  # 去除引用标记
    line = re.sub(r'^[-*]\s+', '', line)  # 去除列表标记
    line = re.sub(r'_{2,}', '', line)  # 去除下划线
    line = re.sub(r'\[[\d]+\]', '', line)  # 去除脚注编号
    # 去除首尾空白
    line = line.strip()
    return line

def detect_section(text, current_section):
    """检测当前所在的条款/章节"""
    # 检测Section/Sec.
    sec_match = re.search(r'\*{0,2}(?:Section|Sec\.)\s+(\d+)[\.\s]', text)
    if sec_match:
        return f"Section {sec_match.group(1)}"
    # 检测子条款 (a), (b), (c)等
    sub_match = re.search(r'^\s*\(([a-z])\)\s', text)
    if sub_match:
        return f"{current_section}({sub_match.group(1)})"
    # 检测数字子条款 (i), (ii)等
    roman_match = re.search(r'^\s*\(([ivx]+)\)\s', text)
    if roman_match:
        return f"{current_section}({roman_match.group(1)})"
    return current_section

def split_into_clauses(text):
    """将文本按小句拆分"""
    # 英文句子结束标点：. ? ! 后跟空格或行尾
    # 但要注意缩写（U.S., Dr., Mr.等）和数字中的小数点
    clauses = []

    # 先按段落拆分
    paragraphs = re.split(r'\n\s*\n', text)

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 使用正则表达式拆分句子
        # 匹配：句号/问号/感叹号 + 空格/换行 + 大写字母或行尾
        # 排除：常见缩写（U.S., Dr., Mr., Mrs., Ms., etc.）
        pattern = r'(?<=[.!?])\s+(?=[A-Z"\'\[])|(?<=[.!?])$'

        sentences = re.split(pattern, para)

        for sent in sentences:
            sent = sent.strip()
            if sent:
                clauses.append(sent)

    return clauses

def process_file(filename, metadata):
    """处理单个文件"""
    filepath = Path("converted_texts") / filename
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # 按行处理
    lines = text.split('\n')

    corpus = []
    current_section = "标题"
    current_subsection = ""
    clause_id = 0
    doc_prefix = filename.replace('.md', '')

    # 跳过开头的标题和元数据
    skip_header = True
    header_lines = 0

    for i, line in enumerate(lines):
        cleaned = clean_line(line)

        # 跳过垃圾行
        if is_garbage_line(line):
            continue

        # 跳过文件开头的元数据行（前10-15行左右）
        if skip_header:
            # 检测正文开始的标志
            if re.match(r'^(Section|Sec\.)\s+\d+', cleaned) or \
               re.match(r'^(By the authority|PURPOSE|POLICY)', cleaned, re.IGNORECASE) or \
               'Ordered:' in cleaned or 'hereby ordered' in cleaned.lower():
                skip_header = False
            else:
                # 检查是否是标题行
                if cleaned.startswith('Table of Contents') or not cleaned:
                    continue
                # 保留文档标题
                if any(keyword in cleaned for keyword in ['Executive Order', 'AI', 'Artificial Intelligence', 'NIST']):
                    clause_id += 1
                    corpus.append({
                        "id": f"{doc_prefix}_{clause_id:04d}",
                        "source": metadata["name"],
                        "source_full": metadata["full_name"],
                        "government": metadata["government"],
                        "section": "标题",
                        "clause": cleaned
                    })
                continue

        # 检测章节标题
        if cleaned.startswith('Pillar') or cleaned.startswith('Section') or \
           cleaned.startswith('Sec.') or re.match(r'^\d+\.\s+', cleaned):
            current_section = cleaned[:80]  # 截断过长的标题
            clause_id += 1
            corpus.append({
                "id": f"{doc_prefix}_{clause_id:04d}",
                "source": metadata["name"],
                "source_full": metadata["full_name"],
                "government": metadata["government"],
                "section": current_section,
                "clause": cleaned
            })
            continue

        # 检测子标题（斜体或特殊格式）
        if re.match(r'^[_\*]+[^_*]+[_\*]+$', cleaned) or \
           (len(cleaned) < 60 and not cleaned.endswith('.')):
            if len(cleaned) > 3:
                current_subsection = cleaned
                clause_id += 1
                corpus.append({
                    "id": f"{doc_prefix}_{clause_id:04d}",
                    "source": metadata["name"],
                    "source_full": metadata["full_name"],
                    "government": metadata["government"],
                    "section": f"{current_section} > {current_subsection}",
                    "clause": cleaned
                })
                continue

        # 检测子条款
        sub_match = re.match(r'^\(([a-z])\)\s+(.+)', cleaned)
        if sub_match:
            sub_label = sub_match.group(1)
            sub_text = sub_match.group(2)
            current_subsection = f"({sub_label})"
            # 拆分这个子条款的句子
            sentences = split_into_clauses(sub_text)
            for sent in sentences:
                clause_id += 1
                corpus.append({
                    "id": f"{doc_prefix}_{clause_id:04d}",
                    "source": metadata["name"],
                    "source_full": metadata["full_name"],
                    "government": metadata["government"],
                    "section": f"{current_section} > ({sub_label})",
                    "clause": sent
                })
            continue

        # 检测列表项
        if cleaned.startswith('- ') or cleaned.startswith('• '):
            list_text = cleaned[2:]
            sentences = split_into_clauses(list_text)
            for sent in sentences:
                clause_id += 1
                corpus.append({
                    "id": f"{doc_prefix}_{clause_id:04d}",
                    "source": metadata["name"],
                    "source_full": metadata["full_name"],
                    "government": metadata["government"],
                    "section": f"{current_section} > 列表",
                    "clause": sent
                })
            continue

        # 普通段落：按句子拆分
        if len(cleaned) > 10:  # 过滤过短的行
            sentences = split_into_clauses(cleaned)
            for sent in sentences:
                clause_id += 1
                corpus.append({
                    "id": f"{doc_prefix}_{clause_id:04d}",
                    "source": metadata["name"],
                    "source_full": metadata["full_name"],
                    "government": metadata["government"],
                    "section": current_section,
                    "clause": sent
                })

    return corpus

def validate_clause(clause):
    """验证小句质量"""
    text = clause["clause"]

    # 过滤过短的小句
    if len(text) < 5:
        return False

    # 过滤纯数字或符号
    if re.match(r'^[\d\s\.\,\-\–\—\*\#\@\$\%\^\&\(\)]+$', text):
        return False

    # 过滤乱码（大量非ASCII字符但不是中文）
    non_ascii = re.findall(r'[^\x00-\x7F]', text)
    if len(non_ascii) > len(text) * 0.3 and not re.search(r'[一-鿿]', text):
        return False

    # 过滤页码格式
    if re.match(r'^\d{1,3}$', text.strip()):
        return False

    # 过滤只有标点
    if re.match(r'^[\.\,\;\:\!\?\-\–\—\s]+$', text):
        return False

    # 过滤脚注标记
    if re.match(r'^\d{1,2}\s+Executive Order', text):
        return False

    return True

def deduplicate_corpus(corpus):
    """去除重复的小句"""
    seen = set()
    unique_corpus = []
    for item in corpus:
        # 使用文本内容作为去重键
        key = item["clause"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique_corpus.append(item)
    return unique_corpus

def main():
    """主处理函数"""
    all_corpus = []

    # 处理每个文件
    for filename, metadata in pdf_files.items():
        print(f"Processing: {filename}")
        corpus = process_file(filename, metadata)
        print(f"  Found {len(corpus)} clauses")
        all_corpus.extend(corpus)

    print(f"\nTotal clauses before cleaning: {len(all_corpus)}")

    # 验证和清理
    valid_corpus = [c for c in all_corpus if validate_clause(c)]
    print(f"Valid clauses after filtering: {len(valid_corpus)}")

    # 去重
    unique_corpus = deduplicate_corpus(valid_corpus)
    print(f"Clauses after deduplication: {len(unique_corpus)}")

    # 重新编号
    for i, item in enumerate(unique_corpus):
        doc_prefix = item["id"].rsplit('_', 1)[0]
        item["id"] = f"{doc_prefix}_{i+1:04d}"

    # 保存结果
    output_file = "clause_corpus.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_corpus, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to: {output_file}")

    # 生成统计信息
    stats = {
        "total_clauses": len(unique_corpus),
        "by_source": {},
        "by_government": {}
    }

    for item in unique_corpus:
        source = item["source"]
        gov = item["government"]
        stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        stats["by_government"][gov] = stats["by_government"].get(gov, 0) + 1

    with open("corpus_stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\nStatistics:")
    print(f"  By source: {stats['by_source']}")
    print(f"  By government: {stats['by_government']}")

if __name__ == "__main__":
    main()
