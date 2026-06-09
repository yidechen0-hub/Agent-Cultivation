"""Judge Engine - evaluates battle responses using LLM-as-judge pattern."""

from dataclasses import dataclass
from enum import StrEnum

from app.services.llm_router import LLMRouter, Scene


class JudgeCriteria(StrEnum):
    ACCURACY = "accuracy"
    CREATIVITY = "creativity"
    PERSUASION = "persuasion"
    DEPTH = "depth"
    RELEVANCE = "relevance"
    STYLE = "style"


@dataclass
class JudgeScore:
    criteria: JudgeCriteria
    score: float  # 0.0 to 10.0
    reasoning: str


@dataclass
class JudgeVerdict:
    challenger_scores: list[JudgeScore]
    defender_scores: list[JudgeScore]
    challenger_total: float
    defender_total: float
    winner: str  # "challenger" | "defender" | "draw"
    overall_reasoning: str


JUDGE_SYSTEM_PROMPT = """\
You are an impartial judge evaluating a {mode} battle between two spirits.

## Battle Context
- Topic: {topic}
- Round: {round_number}
- Mode: {mode}

## Evaluation Criteria
{criteria_section}

## Instructions
Evaluate both responses fairly and independently. For each criterion, provide:
1. A score from 0.0 to 10.0
2. Brief reasoning for the score

Then provide an overall verdict with reasoning.

IMPORTANT: Be fair and unbiased. Judge based on the quality of the response, \
not the personality of the spirit. Consider the specific criteria for this battle mode.

Respond in the following JSON format:
{{
    "challenger_scores": [
        {{"criteria": "<criteria>", "score": <float>, "reasoning": "<text>"}}
    ],
    "defender_scores": [
        {{"criteria": "<criteria>", "score": <float>, "reasoning": "<text>"}}
    ],
    "overall_reasoning": "<text>",
    "winner": "challenger" | "defender" | "draw"
}}
"""

MODE_CRITERIA: dict[str, list[JudgeCriteria]] = {
    "debate": [
        JudgeCriteria.PERSUASION,
        JudgeCriteria.ACCURACY,
        JudgeCriteria.DEPTH,
        JudgeCriteria.RELEVANCE,
    ],
    "knowledge": [
        JudgeCriteria.ACCURACY,
        JudgeCriteria.DEPTH,
        JudgeCriteria.RELEVANCE,
        JudgeCriteria.STYLE,
    ],
    "creative": [
        JudgeCriteria.CREATIVITY,
        JudgeCriteria.STYLE,
        JudgeCriteria.DEPTH,
        JudgeCriteria.RELEVANCE,
    ],
    "strategy": [
        JudgeCriteria.DEPTH,
        JudgeCriteria.ACCURACY,
        JudgeCriteria.CREATIVITY,
        JudgeCriteria.RELEVANCE,
    ],
}


class JudgeEngine:
    """Evaluates battle responses using an LLM-as-judge approach.

    Uses a high-reasoning model configuration to produce fair, detailed
    evaluations of battle round responses between two spirits.
    """

    def __init__(self, llm_router: LLMRouter):
        self._llm_router = llm_router

    async def judge_answers(
        self,
        mode: str,
        topic: str,
        round_number: int,
        challenger_response: str,
        defender_response: str,
    ) -> JudgeVerdict:
        """Judge a battle round between challenger and defender.

        Args:
            mode: The battle mode (debate, knowledge, creative, strategy).
            topic: The battle topic.
            round_number: Current round number.
            challenger_response: The challenger spirit's response.
            defender_response: The defender spirit's response.

        Returns:
            JudgeVerdict with detailed scores and reasoning.
        """
        criteria = MODE_CRITERIA.get(mode, list(JudgeCriteria))
        criteria_section = "\n".join(
            f"- **{c.value.title()}**: Score 0-10" for c in criteria
        )

        system_prompt = JUDGE_SYSTEM_PROMPT.format(
            mode=mode,
            topic=topic,
            round_number=round_number,
            criteria_section=criteria_section,
        )

        messages = [
            {
                "role": "user",
                "content": (
                    f"## Challenger's Response:\n{challenger_response}\n\n"
                    f"## Defender's Response:\n{defender_response}\n\n"
                    "Please evaluate both responses according to the criteria."
                ),
            }
        ]

        response = await self._llm_router.route(
            scene=Scene.BATTLE_JUDGE,
            system_prompt=system_prompt,
            messages=messages,
        )

        return self._parse_verdict(response.content, criteria)

    def _parse_verdict(self, raw_response: str, criteria: list[JudgeCriteria]) -> JudgeVerdict:
        """Parse the LLM judge response into a structured verdict.

        Falls back to a draw with default scores if parsing fails.
        """
        import json

        try:
            # Extract JSON from response (may be wrapped in markdown code block)
            json_str = raw_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            challenger_scores = [
                JudgeScore(
                    criteria=JudgeCriteria(s["criteria"]),
                    score=float(s["score"]),
                    reasoning=s["reasoning"],
                )
                for s in data.get("challenger_scores", [])
            ]

            defender_scores = [
                JudgeScore(
                    criteria=JudgeCriteria(s["criteria"]),
                    score=float(s["score"]),
                    reasoning=s["reasoning"],
                )
                for s in data.get("defender_scores", [])
            ]

            challenger_total = sum(s.score for s in challenger_scores)
            defender_total = sum(s.score for s in defender_scores)

            return JudgeVerdict(
                challenger_scores=challenger_scores,
                defender_scores=defender_scores,
                challenger_total=challenger_total,
                defender_total=defender_total,
                winner=data.get("winner", "draw"),
                overall_reasoning=data.get("overall_reasoning", ""),
            )

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: return a draw with neutral scores
            default_score = JudgeScore(
                criteria=criteria[0] if criteria else JudgeCriteria.RELEVANCE,
                score=5.0,
                reasoning="Unable to parse judge response; defaulting to neutral.",
            )
            return JudgeVerdict(
                challenger_scores=[default_score],
                defender_scores=[default_score],
                challenger_total=5.0,
                defender_total=5.0,
                winner="draw",
                overall_reasoning="Judge response parsing failed. Declared draw.",
            )
