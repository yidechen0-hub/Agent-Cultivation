"""Spirit router - handles spirit-related agent operations."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SpiritProfileResponse(BaseModel):
    spirit_id: UUID
    personality_summary: str
    memory_count: int
    skill_list: list[str]


@router.get("/spirits/{spirit_id}/profile", response_model=SpiritProfileResponse)
async def get_spirit_agent_profile(spirit_id: UUID) -> SpiritProfileResponse:
    """Get the agent profile for a spirit including personality and capabilities."""
    # TODO: Load spirit data and generate agent profile summary
    raise NotImplementedError("Spirit profile endpoint not yet implemented")
