from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies.auth import get_current_user
from backend.repositories.insights_basket_repository import (
    get_insights_basket,
    save_insights_basket,
)
from backend.repositories.insights_repository import (
    list_insights_analysis_by_user,
    save_insights_analysis,
)
from backend.schemas.insights import (
    InsightsAnalyzeRequest,
    InsightsAnalyzeResponse,
    InsightsBasketResponse,
    InsightsBasketSyncRequest,
    InsightsError,
    InsightsHistoryItem,
    InsightsHistoryResponse,
)
from backend.schemas.user import UserOut
from backend.services.insights_service import (
    InsightsServiceError,
    analyze_insights,
)

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.post("/analyze", response_model=InsightsAnalyzeResponse)
def insights_analyze(
    body: InsightsAnalyzeRequest,
    current_user: UserOut = Depends(get_current_user),
) -> InsightsAnalyzeResponse:
    if body.user_id is not None and body.user_id != current_user.id:
        return InsightsAnalyzeResponse(
            success=False,
            error=InsightsError(
                code="AUTH_USER_MISMATCH",
                message="userId 与当前登录用户不一致。",
                retryable=False,
            ),
        )

    try:
        data = analyze_insights(
            current_user.id,
            mode=body.mode,
            selected_log_ids=body.selected_log_ids,
            date_start=body.date_range.start,
            date_end=body.date_range.end,
        )
    except InsightsServiceError as exc:
        return InsightsAnalyzeResponse(
            success=False,
            error=InsightsError(
                code=exc.code,
                message=exc.user_message,
                retryable=exc.retryable,
            ),
        )
    except Exception:
        return InsightsAnalyzeResponse(
            success=False,
            error=InsightsError(
                code="INTERNAL_ERROR",
                message="分析服务出现意外错误，请稍后重试。",
                retryable=True,
            ),
        )

    if body.cache_key and body.cache_key.strip():
        try:
            save_insights_analysis(
                current_user.id,
                cache_key=body.cache_key.strip(),
                mode=body.mode,
                date_start=body.date_range.start,
                date_end=body.date_range.end,
                selected_log_ids=body.selected_log_ids or [],
                result=data,
            )
        except Exception:
            pass

    return InsightsAnalyzeResponse(success=True, data=data)


@router.get("/history", response_model=InsightsHistoryResponse)
def insights_history(
    current_user: UserOut = Depends(get_current_user),
) -> InsightsHistoryResponse:
    records = list_insights_analysis_by_user(current_user.id)
    items = [
        InsightsHistoryItem(cache_key=r["cache_key"], data=r["data"])
        for r in records
    ]
    return InsightsHistoryResponse(items=items)


@router.get("/basket", response_model=InsightsBasketResponse)
def insights_basket(
    current_user: UserOut = Depends(get_current_user),
) -> InsightsBasketResponse:
    try:
        items = get_insights_basket(current_user.id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to load insights basket",
        ) from exc
    return InsightsBasketResponse(items=items)


@router.put("/basket", response_model=InsightsBasketResponse)
def insights_basket_sync(
    body: InsightsBasketSyncRequest,
    current_user: UserOut = Depends(get_current_user),
) -> InsightsBasketResponse:
    try:
        save_insights_basket(
            current_user.id,
            items=body.items,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save insights basket",
        ) from exc
    return InsightsBasketResponse(items=body.items)
