"""Response-схемы статусов задач."""

from pydantic import BaseModel, ConfigDict


class TaskStatusResponse(BaseModel):
    """Публичное представление системного статуса задачи."""

    code: str
    title: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
