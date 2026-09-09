"""Response-схемы типов повторения задач."""

from pydantic import BaseModel, ConfigDict


class TaskRecurrenceTypeResponse(BaseModel):
    """Публичное представление системного типа повторения задачи."""

    code: str
    title: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
