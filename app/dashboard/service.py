"""Application service de leitura do Dashboard."""

from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.core.errors import ForbiddenError
from app.dashboard.queries import buyer_dashboard, ops_dashboard, seller_dashboard
from app.dashboard.schemas import BuyerDashboard, OpsDashboard, SellerDashboard


def get_dashboard(session: Session, user: User) -> SellerDashboard | BuyerDashboard | OpsDashboard:
    """Monta a projecao do Dashboard a partir do usuario autenticado."""
    if user.role == UserRole.SELLER and user.seller_id is not None:
        return seller_dashboard(session, user.seller_id)
    if user.role == UserRole.BUYER:
        return buyer_dashboard(session, user.id)
    if user.role == UserRole.OPS:
        return ops_dashboard(session)
    raise ForbiddenError("Dashboard role required")
