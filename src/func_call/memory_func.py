from langchain_core.tools import tool
from src.database.store import JsonStore
from pathlib import Path
from typing import Literal


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "data.json"
store = JsonStore(DATA_PATH)


@tool(parse_docstring=True)
def get_weather(city: str) -> dict:
    """Возвращает текущую погоду в городе. Вызывай, когда спрашивают про погоду.

    Args:
        city: Название города, например 'Москва'.
    """
    return {"city": city, "temperature": 7, "conditions": "облачно"}


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _short(fact: dict) -> dict:
    """То, что видит модель: без служебного мусора."""
    return {
        "id": fact["id"],
        "subject": fact["subject"],
        "fact": fact["fact"],
        "source": fact["source"],
        "confirmations": fact["confirmations"],
    }


@tool(parse_docstring=True)
def save_fact(
        subject: str,
        fact: str,
        source: Literal["stated", "inferred"],
        priority: Literal[1, 2, 3],
) -> dict:
    """Сохраняет устойчивый факт в долгую память. Вызывай, когда пользователь сообщает что-то о себе или о других людях. Не вызывай для приветствий, болтовни и разовых событий.

    Args:
        subject: О ком факт. 'user' — если о самом пользователе; иначе имя человека, например 'Вася'.
        fact: Короткий факт без имени субъекта, например 'пишет на Python' или 'живёт в Нижнем Новгороде'.
        source: 'stated' — человек сказал это прямо; 'inferred' — твоя догадка.
        priority: 1 — ключевое (имя, город, работа, учёба); 2 — навыки, интересы, привычки; 3 — мелочи.
    """
    subject = subject.strip()
    # Пока дедупликация по точному совпадению текста.
    # Потом здесь будет поиск похожего факта по эмбеддингам.
    for existing in store.find(subject=subject):
        if _normalize(existing["fact"]) == _normalize(fact):
            updated = store.update(
                existing["id"],
                confirmations=existing["confirmations"] + 1,
                # повторное прямое подтверждение «повышает» догадку до факта
                source="stated" if source == "stated" else existing["source"],
            )
            return {"status": "already_known", **_short(updated)}

    new = store.add(
        subject=subject,
        fact=fact.strip(),
        source=source,
        priority=priority,
        confirmations=1,
    )
    return {"status": "saved", **_short(new)}


@tool(parse_docstring=True)
def search_memory(query: str, subject: str = "user") -> dict:
    """Ищет в долгой памяти факты о человеке. Вызывай перед ответом на вопрос о пользователе или о людях, которых он упоминал. Не выдумывай факты — сначала ищи.

    Args:
        query: Что ищем, своими словами, например 'город' или 'язык программирования'. Пустая строка — все факты о человеке.
        subject: О ком ищем: 'user' или имя человека.
    """
    facts = store.find(subject=subject.strip())
    # Пока поиск по словам. Потом заменишь на косинусную близость эмбеддингов.
    words = [w for w in _normalize(query).split() if len(w) > 2]
    if words:
        matched = [f for f in facts if any(w in _normalize(f["fact"]) for w in words)]
        if matched:
            facts = matched
    facts.sort(key=lambda f: (f.get("priority", 3), -f["confirmations"]))
    return {"subject": subject, "found": len(facts), "facts": [_short(f) for f in facts[:10]]}


@tool(parse_docstring=True)
def update_fact(fact_id: str, new_fact: str) -> dict:
    """Заменяет устаревший факт новым. Вызывай, когда новая информация противоречит старой, например человек переехал или сменил работу. Сначала найди старый факт через search_memory, чтобы узнать его id.

    Args:
        fact_id: id факта из search_memory, например 'f_835ed5b4'.
        new_fact: Новый текст факта.
    """
    updated = store.update(fact_id, fact=new_fact.strip(), confirmations=1, source="stated")
    if updated is None:
        return {"status": "error", "message": f"факт {fact_id} не найден"}
    return {"status": "updated", **_short(updated)}


@tool(parse_docstring=True)
def forget_fact(fact_id: str) -> dict:
    """Удаляет факт из памяти. Вызывай только когда пользователь прямо просит что-то забыть. Сначала найди факт через search_memory, чтобы узнать его id.

    Args:
        fact_id: id факта из search_memory.
    """
    if store.delete(fact_id):
        return {"status": "deleted", "id": fact_id}
    return {"status": "error", "message": f"факт {fact_id} не найден"}


MEMORY_TOOLS = [save_fact, search_memory, update_fact, forget_fact]
