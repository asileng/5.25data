import json
import re

def is_invalid_clause(clause):
    """判断是否为无效小句"""
    text = clause["clause"]

    # 过滤目录格式（包含长串点号）
    if re.search(r'\.{5,}', text):
        return True

    # 过滤表格格式（包含多个竖线）
    if text.count('|') > 3:
        return True

    # 过滤页码格式
    if re.match(r'^\d{1,4}$', text.strip()):
        return True

    # 过滤脚注（以数字开头，包含Executive Order等）
    if re.match(r'^\d{1,2}\s+(Executive Order|Federal Register)', text):
        return True

    # 过滤文件路径或URL
    if re.search(r'www\.|http|\.pdf|\.gov', text, re.IGNORECASE):
        return True

    # 过滤页眉页脚
    if 'Federal Register' in text and 'Vol.' in text:
        return True

    # 过滤签名行
    if re.match(r'^(Michael|David|Marco|THE WHITE HOUSE)', text):
        return True

    # 过滤Billing code
    if 'Billing code' in text or 'FR Doc.' in text:
        return True

    # 过滤纯标点
    if re.match(r'^[\.\,\;\:\!\?\-\–\—\*\s]+$', text):
        return True

    # 过滤过短（5-10字符且不是有意义的缩写）
    if len(text) < 10:
        # 允许一些有意义的短语
        short_valid = ['U.S.', 'AI', 'OMB', 'NIST', 'DOE', 'DOD', 'FBI', 'CIA', 'NSA']
        if text.strip() not in short_valid:
            return True

    # 过滤重复内容（如 "Executive Order Executive Order"）
    if re.search(r'(.{5,})\1', text):
        return True

    return False

def split_long_clause(clause, max_length=500):
    """拆分过长的小句"""
    text = clause["clause"]

    if len(text) <= max_length:
        return [clause]

    # 尝试按句子拆分
    # 匹配句号后跟空格和大写字母
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'\[])', text)

    if len(parts) <= 1:
        # 如果无法拆分，保持原样
        return [clause]

    result = []
    for part in parts:
        part = part.strip()
        if len(part) > 10:  # 忽略过短的部分
            new_clause = clause.copy()
            new_clause["clause"] = part
            result.append(new_clause)

    return result if result else [clause]

def fix_section_labels(corpus):
    """修复截断的section标签"""
    for item in corpus:
        section = item["section"]
        # 如果section被截断（以...结尾），尝试修复
        if section.endswith('...') or section.endswith(' > '):
            # 使用原文的前80个字符作为section
            clause_start = item["clause"][:80]
            # 尝试提取section标题
            sec_match = re.match(r'((?:Section|Sec\.)\s+\d+[\.\s].*?)(?:\s*\(|\s*$)', clause_start)
            if sec_match:
                item["section"] = sec_match.group(1)[:100]
            else:
                item["section"] = clause_start

    return corpus

def main():
    # 加载语料
    with open('clause_corpus.json', 'r', encoding='utf-8') as f:
        corpus = json.load(f)

    print(f"Initial corpus size: {len(corpus)}")

    # 修复section标签
    corpus = fix_section_labels(corpus)

    # 过滤无效小句
    valid_corpus = [c for c in corpus if not is_invalid_clause(c)]
    print(f"After filtering invalid: {len(valid_corpus)}")

    # 拆分过长的小句
    expanded_corpus = []
    for clause in valid_corpus:
        expanded_corpus.extend(split_long_clause(clause))
    print(f"After splitting long clauses: {len(expanded_corpus)}")

    # 重新编号
    for i, item in enumerate(expanded_corpus):
        doc_prefix = item["id"].rsplit('_', 1)[0]
        item["id"] = f"{doc_prefix}_{i+1:04d}"

    # 最终去重
    seen = set()
    final_corpus = []
    for item in expanded_corpus:
        key = item["clause"].strip().lower()
        if key not in seen:
            seen.add(key)
            final_corpus.append(item)

    print(f"After final deduplication: {len(final_corpus)}")

    # 保存
    with open('clause_corpus_clean.json', 'w', encoding='utf-8') as f:
        json.dump(final_corpus, f, ensure_ascii=False, indent=2)

    # 统计
    stats = {
        "total_clauses": len(final_corpus),
        "by_source": {},
        "by_government": {}
    }
    for item in final_corpus:
        source = item["source"]
        gov = item["government"]
        stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        stats["by_government"][gov] = stats["by_government"].get(gov, 0) + 1

    print("\nFinal statistics:")
    print(f"  Total: {stats['total_clauses']}")
    print(f"  By source: {stats['by_source']}")
    print(f"  By government: {stats['by_government']}")

    # 长度分布
    lengths = [len(c["clause"]) for c in final_corpus]
    print(f"\nLength statistics:")
    print(f"  Min: {min(lengths)}")
    print(f"  Max: {max(lengths)}")
    print(f"  Avg: {sum(lengths)/len(lengths):.0f}")

if __name__ == "__main__":
    main()
