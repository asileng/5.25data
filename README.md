# 美国AI政策文本句级语料库

## 概述
本语料库包含6份美国人工智能相关政策文本的句级标注数据。

## 文件说明
- `clause_corpus_final.json`: 句级语料库主文件
- `corpus_stats_final.json`: 统计信息
- `rebuild_text.py`: 根据ID重建原文脚本
- `convert_pdfs.py`: PDF转Markdown脚本
- `structure_corpus.py`: 结构化拆分脚本
- `clean_corpus.py`: 数据清理脚本
- `split_clauses_v3.py`: 动词中心拆分脚本

## 语料库统计
| 来源 | 小句数 |
|------|--------|
| Executive Order 14110 (拜登) | 769 |
| NIST AI 100-1 (拜登) | 521 |
| America's AI Action Plan (特朗普) | 249 |
| Executive Order 14192 (特朗普) | 51 |
| Executive Order 14179 (特朗普) | 25 |
| Executive Order 14255 (特朗普) | 14 |

| 政府 | 小句数 |
|------|--------|
| 拜登政府 | 1290 |
| 特朗普政府 | 339 |

## 使用方法
```bash
# 查看可用文档
python rebuild_text.py

# 重建指定文档
python rebuild_text.py 2025-02172
```

## 数据格式
```json
{
  "id": "2025-02172_0001",
  "source": "Executive Order 14179",
  "source_full": "Removing Barriers to American Leadership in Artificial Intelligence",
  "government": "特朗普政府",
  "section": "标题",
  "clause": "Executive Order 14179 of January 23, 2025"
}
```
