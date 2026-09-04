"""Helper-функции для обработки query params."""

from enum import StrEnum

from fastapi.exceptions import RequestValidationError


def parse_csv_enum[EnumType: StrEnum](
    value: str | None,
    enum_type: type[EnumType],
    *,
    param_name: str,
) -> list[EnumType] | None:
    """Разбирает CSV-строку в список StrEnum-значений."""
    if value is None:
        return None

    parts = [part.strip() for part in value.split(",")]
    raw_values = [part for part in parts if part]
    if not raw_values:
        return None

    parsed_values: list[EnumType] = []
    for raw_value in raw_values:
        try:
            parsed_values.append(enum_type(raw_value))
        except ValueError as error:
            allowed_values = ", ".join(member.value for member in enum_type)
            raise RequestValidationError(
                [
                    {
                        "type": "enum",
                        "loc": ("query", param_name),
                        "msg": f"Input should be one of: {allowed_values}",
                        "input": raw_value,
                    }
                ]
            ) from error

    return parsed_values


def normalize_optional_query_text(value: str | None) -> str | None:
    """Очищает опциональный текстовый query param."""
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None
