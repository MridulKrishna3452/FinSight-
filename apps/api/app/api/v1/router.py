from fastapi import APIRouter

from app.api.v1 import alerts, auth, budgets, imports, insights, transactions, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
