from pydantic import BaseModel, Field
from typing import Dict, Any


class ApiRequest(BaseModel):
    api_code: int                           # 요청할 API 코드 (예: 3001)
    data: Dict[str, Any] = Field(default_factory=dict)  # 비즈니스 데이터

    model_config = {"extra": "ignore"}
