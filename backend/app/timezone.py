"""
时区处理模块
统一将 datetime 转换为东八区（中国标准时间 CST）
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 东八区中国标准时间
CST_TIMEZONE = timezone(timedelta(hours=8))


def to_cst_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    将 datetime 转换为东八区中国时间的 ISO 格式字符串

    Args:
        dt: datetime 对象，可以带时区或不带时区

    Returns:
        东八区时间的 ISO 格式字符串，如果输入为 None 则返回 None

    说明:
        - 如果 datetime 没有时区信息，假设为 UTC 时间
        - 输出格式：2024-01-01T12:00:00+08:00
    """
    if dt is None:
        return None

    # 如果 datetime 没有时区信息，假设为 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # 转换为东八区并返回 ISO 格式
    return dt.astimezone(CST_TIMEZONE).isoformat()


def to_cst_datetime_string(dt: Optional[datetime]) -> Optional[str]:
    """
    将 datetime 转换为东八区中国时间的格式化字符串

    Args:
        dt: datetime 对象

    Returns:
        格式化字符串：2024-01-01 12:00:00
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(CST_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
