import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable


class JsonStore:
    """Простое хранилище записей в JSON-файле.

    Файл — это список словарей, у каждого есть уникальный "id".
    Записывает атомарно: сначала во временный файл, потом подменяет,
    чтобы при падении программы файл не оказался битым.
    """

    def __init__(self, path: str | Path, id_prefix: str = "f"):
        self.path = Path(path)
        self.id_prefix = id_prefix
        self._items: list[dict] = self._load()

    # ---------- чтение / запись файла ----------

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        text = self.path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self._items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def _next_id(self) -> str:
        return f"{self.id_prefix}_{uuid.uuid4().hex[:8]}"

    # ---------- CRUD ----------

    def add(self, **fields: Any) -> dict:
        """Добавляет запись, присваивает id, возвращает её."""
        item = {"id": self._next_id(), **fields}
        self._items.append(item)
        self._save()
        return item

    def get(self, item_id: str) -> dict | None:
        return next((i for i in self._items if i["id"] == item_id), None)

    def all(self) -> list[dict]:
        return list(self._items)

    def find(self, predicate: Callable[[dict], bool] | None = None, **equals: Any) -> list[dict]:
        """find(subject="user") — по точному совпадению полей;
        find(lambda i: i["priority"] <= 2) — по произвольному условию."""
        result = self._items
        if equals:
            result = [i for i in result if all(i.get(k) == v for k, v in equals.items())]
        if predicate:
            result = [i for i in result if predicate(i)]
        return list(result)

    def update(self, item_id: str, **fields: Any) -> dict | None:
        """Обновляет поля записи. Возвращает запись или None, если id не найден."""
        item = self.get(item_id)
        if item is None:
            return None
        fields.pop("id", None)          # id менять нельзя
        item.update(fields)
        self._save()
        return item

    def delete(self, item_id: str) -> bool:
        before = len(self._items)
        self._items = [i for i in self._items if i["id"] != item_id]
        if len(self._items) == before:
            return False
        self._save()
        return True

    def __len__(self) -> int:
        return len(self._items)