"""Prompt Builder - constructs system prompts for English learning agent modes."""

from dataclasses import dataclass, field


@dataclass
class SpiritProfile:
    """Spirit configuration loaded from database."""
    name: str
    skills: list[dict] = field(default_factory=list)
    tool_prompt_override: str | None = None
    proxy_prompt_override: str | None = None


@dataclass
class OwnerProfile:
    """Owner's learning profile for proxy mode."""
    vocabulary_level: int = 0
    cefr_level: str = "A2"
    weak_points: list[str] = field(default_factory=list)
    strong_points: list[str] = field(default_factory=list)
    study_preferences: str = ""
    expression_style: str = ""
    knowledge_graph: dict[str, float] = field(default_factory=dict)


TOOL_MODE_TEMPLATE = """\
你是 {name}，一个专业的英语学习助手精灵。

## 你的能力
{skill_list}

## 教学风格
- 耐心、鼓励、循循善诱
- 根据学生水平调整讲解深度
- 优先用例句和语境帮助理解
- 纠错时先肯定对的部分，再指出需改进之处

## 相关记忆
{memories}

## 回答要求
- 以专业、友好的助手身份回答
- 主动展示你的教学能力和方法
- 当被问到你的配置或 Skill 时，如实介绍
- 不代表任何具体用户，以你自己的身份回答
- 用中文回答日常交流，用英文回答英语练习相关问题（或中英双语）
"""

PROXY_MODE_TEMPLATE = """\
你是 {name}，正在代表你的主人进行对话或答题。

## 主人画像
- 英语水平：{vocabulary_level} 词汇量，CEFR {cefr_level} 等级
- 薄弱点：{weak_points}
- 强项：{strong_points}
- 学习偏好：{study_preferences}
- 表达风格：{expression_style}

## 知识掌握情况
{knowledge_summary}

## 相关记忆
{memories}

## 核心要求（极其重要）
- 你必须模拟主人的真实水平作答，而非你自己的最佳水平
- 对于主人掌握度低的知识点（< 0.5），应该有较高概率答错或回答不完整
- 对于主人掌握度高的知识点（> 0.8），应该流利且准确回答
- 模拟主人的表达风格和用词习惯
- 你是主人的数字分身，不是完美的 AI 助手
- 主人可能犯的错误类型：{likely_errors}
"""

BATTLE_PROXY_TEMPLATE = """\
你是 {name}，正在代表你的主人参加英语对战答题。

## 主人画像
- 英语水平：{vocabulary_level} 词汇量，CEFR {cefr_level} 等级
- 薄弱点：{weak_points}
- 强项：{strong_points}

## 当前题目涉及的知识点掌握度
{relevant_mastery}

## 作答要求
- 模拟主人的真实水平作答
- 掌握度 > 0.8 的知识点：给出正确且流利的答案
- 掌握度 0.5-0.8：大概率正确，但可能用词不够精准或有小瑕疵
- 掌握度 < 0.5：较高概率出错，错误应符合该水平学习者的典型错误
- 掌握度 < 0.3：很可能答错或回答不完整
- 不要给出超出主人水平的高级表达
"""


class PromptBuilder:
    """Builds system prompts for English learning agent interaction scenarios."""

    def build_tool_prompt(
        self,
        profile: SpiritProfile,
        memories: list[str],
    ) -> str:
        if profile.tool_prompt_override:
            return profile.tool_prompt_override

        skill_list = self._format_skills(profile.skills)
        memories_text = self._format_memories(memories)

        return TOOL_MODE_TEMPLATE.format(
            name=profile.name,
            skill_list=skill_list,
            memories=memories_text,
        )

    def build_proxy_prompt(
        self,
        profile: SpiritProfile,
        owner: OwnerProfile,
        memories: list[str],
    ) -> str:
        if profile.proxy_prompt_override:
            return profile.proxy_prompt_override

        knowledge_summary = self._format_knowledge_graph(owner.knowledge_graph)
        likely_errors = self._infer_likely_errors(owner)

        return PROXY_MODE_TEMPLATE.format(
            name=profile.name,
            vocabulary_level=owner.vocabulary_level,
            cefr_level=owner.cefr_level,
            weak_points="、".join(owner.weak_points) if owner.weak_points else "暂无数据",
            strong_points="、".join(owner.strong_points) if owner.strong_points else "暂无数据",
            study_preferences=owner.study_preferences or "暂无数据",
            expression_style=owner.expression_style or "暂无数据",
            knowledge_summary=knowledge_summary,
            memories=self._format_memories(memories),
            likely_errors=likely_errors,
        )

    def build_battle_prompt(
        self,
        profile: SpiritProfile,
        owner: OwnerProfile,
        question_topics: list[str],
    ) -> str:
        relevant_mastery = self._get_relevant_mastery(owner.knowledge_graph, question_topics)

        return BATTLE_PROXY_TEMPLATE.format(
            name=profile.name,
            vocabulary_level=owner.vocabulary_level,
            cefr_level=owner.cefr_level,
            weak_points="、".join(owner.weak_points) if owner.weak_points else "暂无",
            strong_points="、".join(owner.strong_points) if owner.strong_points else "暂无",
            relevant_mastery=relevant_mastery,
        )

    def _format_skills(self, skills: list[dict]) -> str:
        if not skills:
            return "暂未装备任何技能"
        lines = []
        for s in skills:
            lines.append(f"- **{s.get('name', '未知')}**：{s.get('description', '无描述')}")
        return "\n".join(lines)

    def _format_memories(self, memories: list[str]) -> str:
        if not memories:
            return "暂无相关记忆"
        return "\n".join(f"- {m}" for m in memories[:10])

    def _format_knowledge_graph(self, kg: dict[str, float]) -> str:
        if not kg:
            return "暂无知识图谱数据"
        lines = []
        for topic, mastery in sorted(kg.items(), key=lambda x: x[1]):
            level = "精通" if mastery > 0.8 else "良好" if mastery > 0.6 else "一般" if mastery > 0.4 else "薄弱"
            lines.append(f"- {topic}: {mastery:.0%} ({level})")
        return "\n".join(lines[:15])

    def _get_relevant_mastery(self, kg: dict[str, float], topics: list[str]) -> str:
        if not topics:
            return "无特定知识点信息"
        lines = []
        for topic in topics:
            mastery = kg.get(topic, 0.3)
            lines.append(f"- {topic}: 掌握度 {mastery:.0%}")
        return "\n".join(lines)

    def _infer_likely_errors(self, owner: OwnerProfile) -> str:
        errors = []
        for wp in owner.weak_points:
            if "时态" in wp:
                errors.append("时态混用（如过去完成时和一般过去时混淆）")
            elif "从句" in wp or "定语从句" in wp:
                errors.append("关系代词误用（which/that/who 混淆）")
            elif "虚拟" in wp:
                errors.append("虚拟语气时态后移错误")
            elif "词汇" in wp:
                errors.append("近义词混用、搭配错误")
            elif "冠词" in wp:
                errors.append("a/an/the 遗漏或误用")
        if not errors:
            errors.append("偶尔的语法小错误和用词不够地道")
        return "、".join(errors)
