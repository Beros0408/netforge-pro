"""
Rule Engine API routes.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...parser_engine.models.device import Device
from ..config import RuleEngineSettings
from ..models.problem import Category, Problem
from ..services.rule_service import RuleService

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])

# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class AnalyseRequest(BaseModel):
    devices: List[Device] = Field(..., description="Parsed device configurations")
    category: Optional[str] = Field(None, description="Limit to category: l2/l3/security")
    rule_id: Optional[str] = Field(None, description="Run a single rule by ID")


class AnalyseResponse(BaseModel):
    problems: List[Problem]
    summary: dict
    total: int


class RuleInfoResponse(BaseModel):
    rule_id: str
    title: str
    category: str
    severity: str


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

_service: Optional[RuleService] = None


def get_rule_service() -> RuleService:
    global _service
    if _service is None:
        _service = RuleService()
    return _service


def init_rule_service(settings: RuleEngineSettings) -> None:
    global _service
    _service = RuleService(settings)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse(
    request: AnalyseRequest,
    service: RuleService = Depends(get_rule_service),
) -> AnalyseResponse:
    """Analyse device configurations and return detected problems."""
    try:
        if request.rule_id:
            problems = service.analyse_by_rule(request.devices, request.rule_id)
        elif request.category:
            try:
                cat = Category(request.category)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category '{request.category}'. Use: l2, l3, security.",
                )
            problems = service.analyse_by_category(request.devices, cat)
        else:
            problems = service.analyse(request.devices)

        return AnalyseResponse(
            problems=problems,
            summary=service.summarise(problems),
            total=len(problems),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")


@router.get("/", response_model=List[RuleInfoResponse])
async def list_rules(
    service: RuleService = Depends(get_rule_service),
) -> List[RuleInfoResponse]:
    """List all available rules and their metadata."""
    return [RuleInfoResponse(**r) for r in service.list_rules()]


@router.get("/{rule_id}", response_model=RuleInfoResponse)
async def get_rule(
    rule_id: str,
    service: RuleService = Depends(get_rule_service),
) -> RuleInfoResponse:
    """Get metadata for a specific rule."""
    info = service.get_rule_info(rule_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")
    return RuleInfoResponse(**info)
