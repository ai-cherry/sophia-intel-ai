from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter(prefix="/costs", tags=["costs"])
class CostSummary(BaseModel):
    total: float
    daily_breakdown: dict[str, float]
    model_breakdown: dict[str, float]
    budget: float
    used: float
    remaining: float
class DailyCost(BaseModel):
    date: str
    cost: float
    model_usage: dict[str, float]
class ModelCost(BaseModel):
    model: str
    total_cost: float
    total_tokens: int
    count: int
@router.get("/summary")
async def get_cost_summary(days: int = 30):
    # Simulated cost data
    return CostSummary(
        total=124.50,
        daily_breakdown={
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"): 4.15 + i * 0.05
            for i in range(days)
        },
        model_breakdown={
            "openai/gpt-5": 62.30,
            "anthropic/claude-sonnet-4": 34.20,
            "google/gemini-2.5-flash": 28.00,
        },
        budget=100.0,
        used=85.0,
        remaining=15.0,
    )
@router.get("/daily")
async def get_daily_costs(days: int = 30):
    # Simulated daily cost data
    return [
        DailyCost(
            date=(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            cost=4.15 + i * 0.05,
            model_usage={
                "openai/gpt-5": 0.65,
                "anthropic/claude-sonnet-4": 0.25,
                "google/gemini-2.5-flash": 0.10,
            },
        )
        for i in range(days)
    ]
@router.get("/models")
async def get_model_costs(limit: int = 10):
    # Simulated model cost data
    return [
        ModelCost(model=model, total_cost=cost, total_tokens=tokens, count=count)
        for model, (cost, tokens, count) in {
            "openai/gpt-5": (62.30, 124600, 15),
            "anthropic/claude-sonnet-4": (34.20, 85500, 12),
            "google/gemini-2.5-flash": (28.00, 56000, 10),
        }.items()
    ][:limit]
