from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    n_results: int = Field(default=5, ge=1, le=20)
    max_distance: float = Field(default=1.2, gt=0, le=3.0)
    doc_id: str | None = None
    
    
class Source(BaseModel):
    page:int
    heading:str
    distance: float
    
class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    cached: bool = False
    
    
AskResponse.model_rebuild()