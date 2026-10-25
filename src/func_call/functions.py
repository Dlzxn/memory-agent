
from langchain_core.tools import tool



@tool(parse_docstring=True)
def get_weather(city: str) -> dict:
    """Возвращает текущую погоду в городе. Вызывай, когда спрашивают про погоду.

    Args:
        city: Название города, например 'Москва'.
    """
    return {"city": city, "temperature": 7, "conditions": "облачно"}
