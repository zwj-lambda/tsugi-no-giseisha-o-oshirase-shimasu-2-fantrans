#!/usr/bin/env python3
"""协作 CSV 译文自检(独立脚本, 仅标准库)。

检查本仓库 master CSV 的译文是否满足回写硬约束, 错误项任一命中即不通过:
  1. role=command 行(引擎指令串)不可改译, 只能留空或保持原文;
  2. 行首控制标记前缀(首个非 ASCII 字符前的连续 ASCII 段)必须原样保留;
  3. 译文每个字符必须可 CP932(JIS X 0208)编码;
  4. 译文 CP932 字节数不得超过原文(等长槽位约束)。
警告项(不判失败, 建议复核): 假名残留 / 译文与原文长度比越界(0.3-3.0) /
「」引号缺失或不配对。

trans 为空的行视为未翻, 跳过不检。覆盖两类 schema: blocks 全表(含 role 列)
与简单表(orig/trans/note 等, 用于 elf/ui/prf)。权威判定以维护者的主仓管线
为准, 本脚本供提交前快速自查。

用法:
    python tools/check_csv.py [文件或目录 ...]
不带参数时按默认范围检查(blocks/ elf/ ui/ prf/)。
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

MARKER_RE = re.compile(r'^([a-z0-9._]+)(?=[^\x00-\x7f])')
KANA_RANGES: tuple[tuple[int, int], ...] = (
    (0x3041, 0x309F), (0x30A1, 0x30FF), (0xFF61, 0xFF9F))
DEFAULT_DIRS = ('blocks', 'elf', 'ui', 'prf')
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RowIssues:
    """单行校验结果。"""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def unencodable_chars(text: str) -> str:
    """列出文本中不可 CP932 编码的字符(去重排序)。

    Args:
        text: 待检查文本。

    Returns:
        不可编码字符串; 全部可编码时为空串。
    """
    parts: list[str] = []
    for char in sorted(set(text)):
        try:
            char.encode('cp932')
        except UnicodeEncodeError:
            parts.append(char)
    return ''.join(parts)


def check_row(orig: str, trans: str, role: str | None) -> RowIssues:
    """校验单行译文。

    Args:
        orig: 原文。
        trans: 译文(空串由调用方先行跳过)。
        role: 行角色(仅 blocks schema 有该列; 简单表传 None)。

    Returns:
        错误与警告列表。
    """
    issues = RowIssues()
    if role == 'command':
        if trans != orig:
            issues.errors.append('command 行(引擎指令)不可改译, 请保持原文或留空')
        return issues
    marker = MARKER_RE.match(orig)
    if marker and not trans.startswith(marker.group(1)):
        issues.errors.append(f'行首控制标记 {marker.group(1)} 未保留')
    bad = unencodable_chars(trans)
    if bad:
        issues.errors.append(f'字符无法以 CP932 编码: {bad[:8]}')
    else:
        trans_bytes = len(trans.encode('cp932'))
        orig_bytes = len(orig.encode('cp932'))
        if trans_bytes > orig_bytes:
            issues.errors.append(
                f'译文 {trans_bytes} 字节超过原文槽宽 {orig_bytes} 字节')
    residue = ''.join(
        c for c in trans if any(lo <= ord(c) <= hi for lo, hi in KANA_RANGES))
    if residue:
        issues.warnings.append(f'疑似假名残留: {residue[:8]}')
    ratio = len(trans) / max(len(orig), 1)
    if not 0.3 <= ratio <= 3.0:
        issues.warnings.append(f'译文/原文长度比异常: {ratio:.2f}')
    if '「' in orig and '「' not in trans:
        issues.warnings.append('原文含「」而译文无引号')
    if trans.count('「') != trans.count('」'):
        issues.warnings.append('译文「」数量不配对')
    return issues


def check_file(path: Path) -> tuple[int, int, int]:
    """校验单个 CSV 文件并打印明细。

    Args:
        path: CSV 路径(utf-8-sig 编码, Excel 可直接编辑)。

    Returns:
        (译文行数, 错误数, 警告数)。
    """
    translated = 0
    errors = 0
    warnings = 0
    details: list[str] = []
    with path.open('r', newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        has_role = 'role' in (reader.fieldnames or [])
        for row in reader:
            trans = row.get('trans') or ''
            if not trans.strip():
                continue
            translated += 1
            role = row.get('role') if has_role else None
            issues = check_row(row.get('orig') or '', trans, role)
            for msg in issues.errors:
                errors += 1
                details.append(f'  第 {reader.line_num} 行: [错误] {msg}')
            for msg in issues.warnings:
                warnings += 1
                details.append(f'  第 {reader.line_num} 行: [警告] {msg}')
    print(f'{path}: 译文 {translated} 行, 错误 {errors}, 警告 {warnings}')
    for line in details:
        print(line)
    return translated, errors, warnings


def collect_targets(args: list[str]) -> list[Path]:
    """把命令行目标展开为待检 CSV 清单。

    Args:
        args: 文件或目录参数; 为空时用默认范围(REPO_ROOT 下 DEFAULT_DIRS)。

    Returns:
        去重排序后的 CSV 文件列表。
    """
    targets: list[Path] = []
    for item in args:
        path = Path(item)
        if path.is_dir():
            targets.extend(sorted(path.rglob('*.csv')))
        elif path.is_file():
            targets.append(path)
        else:
            print(f'跳过不存在的目标: {path}', file=sys.stderr)
    if not args:
        for name in DEFAULT_DIRS:
            dir_path = REPO_ROOT / name
            if dir_path.is_dir():
                targets.extend(sorted(dir_path.rglob('*.csv')))
    return sorted(set(targets))


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。

    Args:
        argv: 命令行参数(默认取 sys.argv)。

    Returns:
        进程退出码: 有错误 1, 否则 0。
    """
    targets = collect_targets(sys.argv[1:] if argv is None else argv)
    if not targets:
        print('未找到待检 CSV 文件', file=sys.stderr)
        return 1
    total_errors = 0
    total_warnings = 0
    for path in targets:
        _, errors, warnings = check_file(path)
        total_errors += errors
        total_warnings += warnings
    print(f'合计: 错误 {total_errors}, 警告 {total_warnings}')
    if total_errors:
        print('存在错误项, 请修正后再提交', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
