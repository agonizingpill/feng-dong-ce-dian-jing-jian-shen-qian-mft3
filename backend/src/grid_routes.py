from fastapi import APIRouter,Depends
from sqlalchemy import select
from .db import db_session
from .auth import current,admin
from .grid_models import ConditionGrid
from .grid_schemas import GridInput
from . import grid_service as grids
router=APIRouter()
@router.get('/condition-grids')
def list_grids(s=Depends(db_session),u=Depends(current)):return [grids.view(s,x) for x in s.scalars(select(ConditionGrid).order_by(ConditionGrid.id.desc()))]
@router.post('/condition-grids')
def create_grid(d:GridInput,s=Depends(db_session),u=Depends(admin)):
    x=grids.create(s,d,u);s.commit();return x
@router.put('/condition-grids/{id}')
def revise_grid(id:int,d:GridInput,s=Depends(db_session),u=Depends(admin)):
    x=grids.revise(s,id,d,u);s.commit();return x
@router.post('/condition-grids/{id}/issue')
def issue_grid(id:int,s=Depends(db_session),u=Depends(admin)):
    x=grids.issue(s,id,u);s.commit();return x
