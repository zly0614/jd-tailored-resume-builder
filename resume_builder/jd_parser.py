from __future__ import annotations

import re
from collections import Counter

from .models import JobDescription

STOPWORDS = {
    "负责",
    "以及",
    "相关",
    "工作",
    "能够",
    "以上",
    "优先",
    "熟悉",
    "具备",
    "岗位",
    "职责",
    "我们",
    "参与",
    "进行",
    "通过",
    "团队",
    "经验",
    "能力",
    "建设",
    "优化",
    "方案",
    "业务",
    "产品",
    "系统",
    "技术",
    "开发",
    "设计",
    "实施",
    "to",
    "and",
    "the",
    "with",
    "for",
    "you",
    "will",
    "that",
    "from",
}


def parse_job_description(raw_text: str, keyword_limit: int = 20) -> JobDescription:
    normalized = re.sub(r"[^\w\u4e00-\u9fff#+./-]+", " ", raw_text.lower())
    tokens = [token.strip() for token in normalized.split() if len(token.strip()) >= 2]

    frequencies = Counter(token for token in tokens if token not in STOPWORDS)
    keywords = [item for item, _count in frequencies.most_common(keyword_limit)]

    responsibilities = []
    for line in raw_text.splitlines():
        cleaned = line.strip(" -•\t")
        if len(cleaned) >= 8:
            responsibilities.append(cleaned)

    return JobDescription(raw_text=raw_text, keywords=keywords, responsibilities=responsibilities)
