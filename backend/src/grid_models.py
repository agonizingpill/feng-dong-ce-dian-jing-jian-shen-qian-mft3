from sqlalchemy import String,Float,JSON,ForeignKey,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class ConditionGrid(Base):
    __tablename__='condition_grids'
    __table_args__=(CheckConstraint("state in ('draft','issued')"),CheckConstraint('mae_limit > 0'))
    id:Mapped[int]=mapped_column(primary_key=True)
    layout_id:Mapped[int]=mapped_column(ForeignKey('layouts.id'))
    code:Mapped[str]=mapped_column(String(60),unique=True)
    speed_intervals:Mapped[list]=mapped_column(JSON)
    angle_intervals:Mapped[list]=mapped_column(JSON)
    mae_limit:Mapped[float]=mapped_column(Float)
    cells:Mapped[list|None]=mapped_column(JSON,nullable=True)
    state:Mapped[str]=mapped_column(String(20),default='draft')
    issued_by:Mapped[str|None]=mapped_column(String(100),nullable=True)
    issued_at:Mapped[str|None]=mapped_column(String(40),nullable=True)
