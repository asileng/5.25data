"""
小句拆分 v3：更智能的拆分逻辑
"""
import json
import re

def split_long_clause(text, max_length=300):
    """拆分过长的小句"""
    if len(text) <= max_length:
        return [text]

    results = []

    # 策略1：按分号拆分
    if ';' in text:
        parts = text.split(';')
        for part in parts:
            part = part.strip()
            if part:
                results.extend(split_long_clause(part, max_length))
        if results:
            return results

    # 策略2：按逗号+and/but/or拆分（并列结构）
    pattern = r',\s*(?:and|but|or)\s+'
    if re.search(pattern, text):
        parts = re.split(pattern, text)
        if len(parts) > 1:
            for i, part in enumerate(parts):
                part = part.strip()
                if part:
                    if i > 0:
                        # 重新加上连词
                        part = 'and ' + part
                    results.extend(split_long_clause(part, max_length))
            if results:
                return results

    # 策略3：按逗号拆分（但要小心不要过度拆分）
    # 只在逗号后跟大写字母时拆分
    if ', ' in text:
        parts = re.split(r',\s+(?=[A-Z])', text)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if part:
                    results.extend(split_long_clause(part, max_length))
            if results:
                return results

    # 策略4：按句号+空格拆分
    if '. ' in text:
        parts = re.split(r'\.\s+(?=[A-Z])', text)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if part:
                    if not part.endswith('.'):
                        part = part + '.'
                    results.extend(split_long_clause(part, max_length))
            if results:
                return results

    # 如果无法拆分，返回原文
    return [text]

def improved_split(text):
    """改进的拆分逻辑"""
    if not text or len(text.strip()) < 10:
        return [text]

    text = text.strip()

    # 先尝试动词中心拆分
    from split_clauses_v2 import split_clause_by_verb_center
    parts = split_clause_by_verb_center(text)

    # 然后对每个部分进行长度检查
    final_parts = []
    for part in parts:
        if len(part) > 300:
            # 进一步拆分
            sub_parts = split_long_clause(part, 300)
            final_parts.extend(sub_parts)
        else:
            final_parts.append(part)

    return final_parts

def process_corpus():
    with open('clause_corpus_clean.json', 'r', encoding='utf-8') as f:
        corpus = json.load(f)

    print(f"Original: {len(corpus)}")

    new_corpus = []
    for item in corpus:
        parts = improved_split(item['clause'])
        for part in parts:
            new_item = item.copy()
            new_item['clause'] = part
            new_corpus.append(new_item)

    print(f"After split: {len(new_corpus)}")

    # 重新编号
    for i, item in enumerate(new_corpus):
        doc_prefix = item['id'].rsplit('_', 1)[0]
        item['id'] = f"{doc_prefix}_{i+1:04d}"

    # 过滤过短的
    new_corpus = [c for c in new_corpus if len(c['clause']) >= 10]
    print(f"After filter: {len(new_corpus)}")

    # 保存
    with open('clause_corpus_v3.json', 'w', encoding='utf-8') as f:
        json.dump(new_corpus, f, ensure_ascii=False, indent=2)

    # 统计
    from collections import Counter
    print("\nBy government:")
    for gov, count in Counter(c['government'] for c in new_corpus).most_common():
        print(f"  {gov}: {count}")

    lengths = [len(c['clause']) for c in new_corpus]
    print(f"\nLength: min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)/len(lengths):.0f}")

    # 检查最长的
    sorted_c = sorted(new_corpus, key=lambda x: len(x['clause']), reverse=True)
    print("\nTop 3 longest:")
    for item in sorted_c[:3]:
        print(f"  {item['id']}: {len(item['clause'])} chars")

if __name__ == "__main__":
    process_corpus()
