"""审查规则配置加载器

加载 .pr-reviewer.json 配置文件，注入到 AI prompt 中。
配置优先级：项目根目录 .pr-reviewer.json > 内置默认规则
"""
import json
import os
from typing import Dict, List, Optional


DEFAULT_RULES = {
    "security": {"enabled": True},
    "correctness": {"enabled": True},
    "performance": {"enabled": True},
    "code_quality": {"enabled": True},
    "best_practices": {"enabled": True},
}


class RuleConfig:
    """审查规则配置"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load(config_path)

    def _find_config(self) -> Optional[str]:
        """向上搜索 .pr-reviewer.json"""
        search_dir = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):
            path = os.path.join(search_dir, '.pr-reviewer.json')
            if os.path.exists(path):
                return path
            parent = os.path.dirname(search_dir)
            if parent == search_dir:
                break
            search_dir = parent
        return None

    def _load(self, config_path: Optional[str]) -> Dict:
        path = config_path or self._find_config()
        if not path:
            return {"rules": DEFAULT_RULES, "custom_rules": [], "ignore_patterns": []}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"rules": DEFAULT_RULES, "custom_rules": [], "ignore_patterns": []}

    @property
    def enabled_rules(self) -> List[str]:
        """返回已启用的规则类别名称列表"""
        rules = self.config.get("rules", DEFAULT_RULES)
        return [name for name, cfg in rules.items() if cfg.get("enabled", True)]

    @property
    def custom_rules(self) -> List[Dict]:
        """返回自定义规则列表"""
        return self.config.get("custom_rules", [])

    @property
    def ignore_patterns(self) -> List[str]:
        return self.config.get("ignore_patterns", [])

    def build_rules_prompt(self) -> str:
        """构建注入到 AI prompt 的规则描述"""
        parts = ["## 用户自定义审查规则\n"]

        enabled = self.enabled_rules
        if enabled:
            parts.append("### 启用的审查维度")
            rule_descriptions = self.config.get("rules", DEFAULT_RULES)
            for name in enabled:
                desc = rule_descriptions.get(name, {}).get("description", name)
                parts.append(f"- **{name}**: {desc}")

        custom = self.custom_rules
        if custom:
            parts.append("\n### 自定义规则")
            for i, rule in enumerate(custom, 1):
                severity = rule.get("severity", "warning")
                parts.append(f"{i}. [{severity}] **{rule['name']}**: {rule.get('description', '')}")

        ignored = self.ignore_patterns
        if ignored:
            parts.append(f"\n### 忽略文件\n以下文件模式无需审查: {', '.join(ignored)}")

        return "\n".join(parts) + "\n"
