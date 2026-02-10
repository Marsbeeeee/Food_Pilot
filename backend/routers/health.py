from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def status_check():
    return {"status": "ok"}
