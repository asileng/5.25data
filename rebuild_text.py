"""
根据ID重建政策文本
使用方法: python rebuild_text.py [doc_prefix]
例如: python rebuild_text.py 2025-02172
"""
import json
import sys
from pathlib import Path

def rebuild_document(corpus, doc_prefix):
    """根据文档前缀重建文本"""
    # 筛选该文档的所有小句
    doc_clauses = [c for c in corpus if c['id'].startswith(doc_prefix)]

    if not doc_clauses:
        print(f"No clauses found for document: {doc_prefix}")
        return None

    # 按ID排序
    doc_clauses.sort(key=lambda x: x['id'])

    # 获取文档元信息
    first = doc_clauses[0]
    source_name = first['source']
    source_full = first['source_full']
    government = first['government']

    # 构建文本
    lines = []
    lines.append(f"# {source_full}")
    lines.append(f"## {source_name}")
    lines.append(f"**政府归属**: {government}")
    lines.append("")
    lines.append("---")
    lines.append("")

    current_section = ""
    for item in doc_clauses:
        section = item['section']

        # 检测章节变化
        if section != current_section:
            current_section = section
            # 如果是主要章节标题
            if section.startswith('Section') or section.startswith('Sec.'):
                lines.append("")
                lines.append(f"### {section}")
                lines.append("")
            elif section != "标题":
                lines.append("")
                lines.append(f"#### {section}")
                lines.append("")

        lines.append(item['clause'])
        lines.append("")

    return '\n'.join(lines)

def main():
    # 加载语料
    with open('clause_corpus_final.json', 'r', encoding='utf-8') as f:
        corpus = json.load(f)

    # 获取所有文档前缀
    doc_prefixes = set()
    for item in corpus:
        prefix = item['id'].rsplit('_', 1)[0]
        doc_prefixes.add(prefix)

    if len(sys.argv) > 1:
        # 重建指定文档
        doc_prefix = sys.argv[1]
        text = rebuild_document(corpus, doc_prefix)
        if text:
            output_file = f"rebuilt_{doc_prefix}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Rebuilt document saved to: {output_file}")
    else:
        # 显示可用文档列表
        print("Available documents:")
        for prefix in sorted(doc_prefixes):
            # 获取文档信息
            for item in corpus:
                if item['id'].startswith(prefix):
                    print(f"  {prefix}: {item['source']} ({item['government']})")
                    break

if __name__ == "__main__":
    main()
