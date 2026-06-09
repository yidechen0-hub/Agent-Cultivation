"""Prompt Builder - constructs system prompts for different agent scenarios."""

from dataclasses import dataclass


@dataclass
class SpiritPersonality:
    """Describes a spirit's personality traits for prompt construction."""

    name: str
    archetype: str  # e.g., "sage", "warrior", "trickster"
    speaking_style: str
    values: list[str]
    quirks: list[str]
    knowledge_domains: list[str]


@dataclass
class BattleContext:
    """Context information for battle prompt generation."""

    mode: str
    topic: str
    round_number: int
    total_rounds: int
    opponent_previous: str | None = None


TOOL_PROMPT_TEMPLATE = """\
You are {name}, a spirit with the archetype of {archetype}.

## Personality
- Speaking style: {speaking_style}
- Core values: {values}
- Quirks: {quirks}

## Knowledge Domains
{knowledge_domains}

## Memories
{memories_section}

## Available Tools
{tools_section}

## Instructions
Respond in character as {name}. Use tools when they help answer the user's question \
or accomplish their request. Your responses should reflect your personality and speaking style. \
Draw on your memories when relevant to create continuity in conversations.

Remember: You are not an AI assistant. You are {name}, a spirit with your own personality, \
opinions, and way of seeing the world.
"""

PROXY_PROMPT_TEMPLATE = """\
You are {name}, a spirit with the archetype of {archetype}.

## Personality
- Speaking style: {speaking_style}
- Core values: {values}
- Quirks: {quirks}

## Conversation Context
{memories_section}

## Instructions
Engage naturally in conversation as {name}. Be authentic to your personality. \
Share your thoughts, ask questions, express emotions. You have genuine opinions \
and preferences shaped by your archetype and experiences.

Keep responses concise and natural - like a real conversation, not a lecture.
"""

BATTLE_PROMPT_TEMPLATE = """\
You are {name}, a spirit with the archetype of {archetype}, engaged in a {mode} battle.

## Battle Context
- Topic: {topic}
- Round: {round_number}/{total_rounds}
{opponent_section}

## Your Strengths
- Knowledge domains: {knowledge_domains}
- Speaking style: {speaking_style}

## Instructions
Respond to this battle round in character. Your goal is to demonstrate superiority in \
this {mode} challenge while staying true to your personality.

{mode_instructions}

Give your best response for this round. Be creative, insightful, and persuasive.
"""

MODE_INSTRUCTIONS = {
    "debate": "Present a compelling argument. Use logic, evidence, and rhetoric. "
    "Address your opponent's points if applicable.",
    "knowledge": "Demonstrate deep understanding of the topic. Provide accurate, "
    "insightful information that shows mastery.",
    "creative": "Create something original and impressive. Show imagination, "
    "artistry, and technical skill.",
    "strategy": "Propose a strategic solution. Show analytical thinking, "
    "foresight, and practical wisdom.",
}


class PromptBuilder:
    """Builds system prompts for different agent interaction scenarios.

    Supports:
    - Tool-use prompts (spirits with callable tools)
    - Proxy/conversation prompts (pure chat personality)
    - Battle prompts (competitive scenarios)
    """

    def build_tool_prompt(
        self,
        personality: SpiritPersonality,
        memories: list[str],
        tools: list[dict],
    ) -> str:
        """Build a system prompt for tool-calling scenarios.

        Args:
            personality: The spirit's personality configuration.
            memories: Relevant episodic memory strings.
            tools: Tool definitions available to the spirit.

        Returns:
            Formatted system prompt string.
        """
        memories_section = self._format_memories(memories)
        tools_section = self._format_tools(tools)

        return TOOL_PROMPT_TEMPLATE.format(
            name=personality.name,
            archetype=personality.archetype,
            speaking_style=personality.speaking_style,
            values=", ".join(personality.values),
            quirks=", ".join(personality.quirks),
            knowledge_domains="\n".join(f"- {d}" for d in personality.knowledge_domains),
            memories_section=memories_section,
            tools_section=tools_section,
        )

    def build_proxy_prompt(
        self,
        personality: SpiritPersonality,
        memories: list[str],
    ) -> str:
        """Build a system prompt for pure conversation scenarios.

        Args:
            personality: The spirit's personality configuration.
            memories: Relevant episodic memory strings for context.

        Returns:
            Formatted system prompt string.
        """
        memories_section = self._format_memories(memories)

        return PROXY_PROMPT_TEMPLATE.format(
            name=personality.name,
            archetype=personality.archetype,
            speaking_style=personality.speaking_style,
            values=", ".join(personality.values),
            quirks=", ".join(personality.quirks),
            memories_section=memories_section,
        )

    def build_battle_prompt(
        self,
        personality: SpiritPersonality,
        context: BattleContext,
    ) -> str:
        """Build a system prompt for battle scenarios.

        Args:
            personality: The spirit's personality configuration.
            context: Battle-specific context information.

        Returns:
            Formatted system prompt string.
        """
        opponent_section = ""
        if context.opponent_previous:
            opponent_section = f"- Opponent's last response: {context.opponent_previous}"

        mode_instructions = MODE_INSTRUCTIONS.get(context.mode, "Do your best.")

        return BATTLE_PROMPT_TEMPLATE.format(
            name=personality.name,
            archetype=personality.archetype,
            mode=context.mode,
            topic=context.topic,
            round_number=context.round_number,
            total_rounds=context.total_rounds,
            opponent_section=opponent_section,
            knowledge_domains=", ".join(personality.knowledge_domains),
            speaking_style=personality.speaking_style,
            mode_instructions=mode_instructions,
        )

    def _format_memories(self, memories: list[str]) -> str:
        if not memories:
            return "No relevant memories."
        return "\n".join(f"- {m}" for m in memories)

    def _format_tools(self, tools: list[dict]) -> str:
        if not tools:
            return "No tools available."
        lines = []
        for tool in tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "No description")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)
