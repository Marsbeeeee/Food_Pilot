from fastapi import APIRouter, Depends

from backend.dependencies.auth import get_current_user
from backend.schemas.insights import (
    InsightsAnalyzeRequest,
    InsightsAnalyzeResponse,
    InsightsError,
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

    return InsightsAnalyzeResponse(success=True, data=data)
