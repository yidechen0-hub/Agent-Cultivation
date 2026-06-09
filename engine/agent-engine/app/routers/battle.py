"""Battle router - handles battle creation and result retrieval."""

from uuid import UUID, uuid4
from enum import StrEnum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class BattleMode(StrEnum):
    DEBATE = "debate"
    KNOWLEDGE = "knowledge"
    CREATIVE = "creative"
    STRATEGY = "strategy"


class CreateBattleRequest(BaseModel):
    challenger_spirit_id: UUID
    defender_spirit_id: UUID
    mode: BattleMode
    topic: str | None = None
    season_id: UUID | None = None


class BattleResponse(BaseModel):
    battle_id: UUID
    status: str
    challenger_spirit_id: UUID
    defender_spirit_id: UUID
    mode: BattleMode


class BattleRound(BaseModel):
    round_number: int
    challenger_response: str
    defender_response: str
    judge_scores: dict[str, float]
    judge_reasoning: str


class BattleResult(BaseModel):
    battle_id: UUID
    status: str  # "pending" | "in_progress" | "completed"
    winner_spirit_id: UUID | None = None
    rounds: list[BattleRound] = []
    total_scores: dict[str, float] = {}
    elo_changes: dict[str, int] = {}


@router.post("/battles", response_model=BattleResponse)
async def create_battle(request: CreateBattleRequest) -> BattleResponse:
    """Create a new battle between two spirits.

    The battle engine will:
    1. Validate both spirits exist and are eligible
    2. Generate a battle topic if not provided
    3. Initialize battle rounds based on mode
    4. Queue the battle for async processing via NATS
    """
    battle_id = uuid4()

    # TODO: Validate spirits exist and are not already in battle
    # TODO: Publish battle event to NATS for async processing
    # TODO: Persist battle record to database

    return BattleResponse(
        battle_id=battle_id,
        status="pending",
        challenger_spirit_id=request.challenger_spirit_id,
        defender_spirit_id=request.defender_spirit_id,
        mode=request.mode,
    )


@router.get("/battles/{battle_id}/result", response_model=BattleResult)
async def get_battle_result(battle_id: UUID) -> BattleResult:
    """Get the result of a battle.

    Returns current state including completed rounds, scores, and ELO changes
    once the battle is finished.
    """
    # TODO: Fetch battle from database
    # TODO: If battle is still in progress, return partial results

    raise HTTPException(
        status_code=404,
        detail=f"Battle {battle_id} not found",
    )
