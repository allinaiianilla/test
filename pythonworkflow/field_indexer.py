"""
Field Indexer — 字段索引查找器

在 all_fields 列表中查找 tech_fields 的索引位置。
"""

from typing import List, Dict


def find_tech_indexes(all_fields: List[str], tech_fields: List[str]) -> List[int]:
    """
    返回 all_fields 中属于技术字段的元素的索引列表。

    Args:
        all_fields: 所有字段列表
        tech_fields: 技术字段列表

    Returns:
        技术字段在 all_fields 中的索引列表

    Examples:
        >>> find_tech_indexes(
        ...     ["Name", "CPU", "Price", "RAM", "Weight", "GPU", "Color"],
        ...     ["CPU", "RAM", "GPU", "SSD"]
        ... )
        [1, 3, 5]
    """
    tech_set = set(tech_fields)
    return [i for i, field in enumerate(all_fields) if field in tech_set]


def find_tech_indexes_with_names(
    all_fields: List[str], tech_fields: List[str]
) -> List[Dict]:
    """
    返回 all_fields 中技术字段的索引及字段名。

    Args:
        all_fields: 所有字段列表
        tech_fields: 技术字段列表

    Returns:
        包含 index 和 field 的字典列表

    Examples:
        >>> find_tech_indexes_with_names(
        ...     ["Name", "CPU", "Price", "RAM"],
        ...     ["CPU", "RAM"]
        ... )
        [{'index': 1, 'field': 'CPU'}, {'index': 3, 'field': 'RAM'}]
    """
    tech_set = set(tech_fields)
    return [
        {"index": i, "field": field}
        for i, field in enumerate(all_fields)
        if field in tech_set
    ]


class FieldIndexer:
    """字段索引查找器（适合重复查询场景）"""

    def __init__(self, tech_fields: List[str]):
        self._tech_set = set(tech_fields)

    def find(self, all_fields: List[str]) -> List[int]:
        """返回索引列表"""
        return [i for i, f in enumerate(all_fields) if f in self._tech_set]

    def find_with_names(self, all_fields: List[str]) -> List[Dict]:
        """返回索引+字段名列表"""
        return [
            {"index": i, "field": f}
            for i, f in enumerate(all_fields)
            if f in self._tech_set
        ]


if __name__ == "__main__":
    # 快速验证
    all_fields = ["Name", "CPU", "Price", "RAM", "Weight", "GPU", "Color"]
    tech_fields = ["CPU", "RAM", "GPU", "SSD"]

    # 方式一：函数
    print("索引:", find_tech_indexes(all_fields, tech_fields))
    print("详情:", find_tech_indexes_with_names(all_fields, tech_fields))

    # 方式二：类（多次查询更高效）
    indexer = FieldIndexer(tech_fields)
    print("类-索引:", indexer.find(all_fields))
    print("类-详情:", indexer.find_with_names(all_fields))
