from pydantic import BaseModel,Field,field_validator,model_validator
class Interval(BaseModel):
    lo:float=Field(allow_inf_nan=False)
    hi:float=Field(allow_inf_nan=False)
    @model_validator(mode='after')
    def ordered(self):
        if not self.lo<self.hi:raise ValueError('区间下限须小于上限')
        return self
class GridInput(BaseModel):
    layout_id:int
    code:str=Field(min_length=4,max_length=60)
    mae_limit:float=Field(gt=0,le=1000,allow_inf_nan=False)
    speed_intervals:list[Interval]=Field(min_length=1,max_length=8)
    angle_intervals:list[Interval]=Field(min_length=1,max_length=8)
    @field_validator('code')
    @classmethod
    def code_not_empty(cls,v):
        if not v.strip():raise ValueError('工况表编号不能为空')
        return v.strip()
