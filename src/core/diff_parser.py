"""
diff_parser.py - 解析 PR diff，拆分成结构化数据

核心功能：
1. 把完整 diff 按文件拆分
2. 提取每个文件的改动统计（+/- 行数）
3. 返回结构化数据供 AI reviewer 使用
"""

import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class FileDiff:
    """单个文件的 diff 信息"""
    filename: str              # 文件路径
    old_path: str             # 原路径 (a/...)
    new_path: str             # 新路径 (b/...)
    status: str               # modified / added / deleted / renamed
    additions: int            # 新增行数
    deletions: int            # 删除行数
    diff_content: str         # 完整 diff 文本


class DiffParser:
    """Diff 解析器"""
    
    def __init__(self, diff_text: str):
        """
        初始化解析器
        
        Args:
            diff_text: 完整的 diff 文本
        """
        self.diff_text = diff_text
        self.file_diffs: List[FileDiff] = []
    
    def parse(self) -> List[FileDiff]:
        """
        解析 diff，拆分成多个文件的改动
        
        Returns:
            文件 diff 列表
        """
        # 按 "diff --git" 拆分（每个文件块以这行开头）
        # 用 (?=...) 前向匹配保留分隔符本身
        file_blocks = re.split(r'(?<=\n)(?=diff --git )', self.diff_text)
        
        for block in file_blocks:
            if not block.strip():
                continue
            
            file_diff = self._parse_file_block(block)
            if file_diff:
                self.file_diffs.append(file_diff)
        
        return self.file_diffs
    
    def _parse_file_block(self, block: str) -> Optional[FileDiff]:
        """
        解析单个文件的 diff 块
        
        Args:
            block: 单个文件的 diff 文本
            
        Returns:
            FileDiff 对象
        """
        # 提取文件路径
        # 格式：diff --git a/path/to/file b/path/to/file
        header_match = re.match(r'diff --git a/(.+?) b/(.+?)(?:\n|$)', block)
        if not header_match:
            return None
        
        old_path = header_match.group(1)
        new_path = header_match.group(2)
        
        # 判断文件状态
        status = self._determine_status(block, old_path, new_path)
        
        # 文件名：新路径（删除文件用旧路径）
        filename = new_path if status != 'deleted' else old_path
        
        # 统计 +/− 行数
        additions, deletions = self._count_changes(block)

        annotated = self._annotate_line_numbers(block)

        return FileDiff(
            filename=filename,
            old_path=old_path,
            new_path=new_path,
            status=status,
            additions=additions,
            deletions=deletions,
            diff_content=annotated
        )
    
    def _determine_status(self, block: str, old_path: str, new_path: str) -> str:
        """
        判断文件状态：modified / added / deleted / renamed
        
        Args:
            block: diff 文本块
            old_path: 原路径
            new_path: 新路径
            
        Returns:
            状态字符串
        """
        # 检查是否是新文件（新增）
        if re.search(r'new file mode \d+', block):
            return 'added'
        
        # 检查是否是删除的文件
        if re.search(r'deleted file mode \d+', block):
            return 'deleted'
        
        # 检查是否重命名
        if old_path != new_path:
            return 'renamed'
        
        # 默认是修改
        return 'modified'
    
    def _annotate_line_numbers(self, block: str) -> str:
        """
        给 diff 内容每一行标注新文件行号，让 AI 能报告精确行号。
        @@ -10,6 +10,12 @@ → 新文件从第 10 行开始。
        上下文行和 + 行计入行号，- 行不加（显示旧行号位置）。
        """
        lines = block.split('\n')
        result = []
        new_lineno = 0

        for line in lines:
            hunk_match = re.match(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            if hunk_match:
                new_lineno = int(hunk_match.group(2))
                result.append(line)
                continue

            if line.startswith(('diff --git', 'index ', '--- ', '+++ ', '@@ ', '\\ ', 'new file', 'deleted file', 'old mode', 'new mode', 'rename ', 'similarity ', 'Binary files')):
                result.append(line)
                continue

            if line.startswith('-') and not line.startswith('---'):
                result.append(f"     {line}")
                continue

            prefix = f"{new_lineno:4d}: "
            result.append(f"{prefix}{line}")
            new_lineno += 1

        return '\n'.join(result)

    def _count_changes(self, block: str) -> tuple:
        """
        统计新增和删除的行数
        
        Args:
            block: diff 文本块
            
        Returns:
            (additions, deletions) 元组
        """
        additions = 0
        deletions = 0
        
        for line in block.split('\n'):
            # 跳过 diff 元信息行
            if line.startswith('diff --git') or \
               line.startswith('index ') or \
               line.startswith('--- ') or \
               line.startswith('+++ ') or \
               line.startswith('@@ '):
                continue
            
            # 统计 +/− 开头的行（但要排除 diff 头部的 +++ ---）
            if line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        return additions, deletions
    
    def get_line_context(self, filename: str, line_number: int, context_lines: int = 3):
        """
        提取指定文件某个行号的前后代码上下文

        Returns:
            dict 或 None
        """
        for fd in self.file_diffs:
            if self._match_filename(fd, filename):
                return self._extract_context(fd.diff_content, line_number, context_lines, fd.filename)
        return None

    @staticmethod
    def _match_filename(file_diff, target: str) -> bool:
        candidates = {file_diff.filename, file_diff.new_path, file_diff.old_path}
        for c in candidates:
            if c == target or c == f"b/{target}" or c == f"a/{target}":
                return True
        basenames = {os.path.basename(p) for p in candidates if p}
        return os.path.basename(target) in basenames

    @staticmethod
    def _extract_context(diff_content: str, target_line: int, context_lines: int, filename: str):
        line_map = {}
        for line in diff_content.split('\n'):
            m = re.match(r'^\s*(\d+):\s(.*)', line)
            if m:
                line_map[int(m.group(1))] = m.group(2)

        if target_line not in line_map:
            return None

        all_nos = sorted(line_map.keys())
        idx = all_nos.index(target_line)
        start = max(0, idx - context_lines)
        end = min(len(all_nos), idx + context_lines + 1)

        context_nos = all_nos[start:end]
        return {
            "filename": filename,
            "target_line": target_line,
            "lines": [(ln, line_map[ln]) for ln in context_nos],
            "target_index": context_nos.index(target_line),
        }

    def get_summary(self) -> Dict:
        """
        获取整个 diff 的摘要信息
        
        Returns:
            摘要字典
        """
        total_additions = sum(f.additions for f in self.file_diffs)
        total_deletions = sum(f.deletions for f in self.file_diffs)
        
        return {
            "files_changed": len(self.file_diffs),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "files": [
                {
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions
                }
                for f in self.file_diffs
            ]
        }
