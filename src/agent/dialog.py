import os


class Color:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


class Dialog:
    """Консольный чат с агентом.

    Команды:
        /help    — список команд
        /memory  — что агент помнит (если передан store)
        /clear   — очистить историю диалога (память о пользователе остаётся)
        /exit    — выйти
    """

    def __init__(self, agent, store=None, assistant_name: str = "Ассистент"):
        self.agent = agent
        self.store = store
        self.name = assistant_name
        os.system("")  # включает цвета в консоли Windows

    # ---------- вывод ----------

    def _say(self, text: str) -> None:
        print(f"{Color.GREEN}{Color.BOLD}{self.name}:{Color.RESET} {text}\n")

    def _info(self, text: str) -> None:
        print(f"{Color.DIM}{text}{Color.RESET}")

    def _error(self, text: str) -> None:
        print(f"{Color.RED}Ошибка: {text}{Color.RESET}\n")

    def _greeting(self) -> None:
        line = "─" * 50
        print(f"\n{Color.CYAN}{line}")
        print(f"  {self.name} с долгой памятью")
        print(f"  /help — команды, /exit — выход")
        print(f"{line}{Color.RESET}\n")

    # ---------- команды ----------

    def _help(self) -> None:
        self._info("/memory — что я помню о тебе\n/clear  — начать диалог заново\n/exit   — выйти\n")

    def _memory(self) -> None:
        if self.store is None:
            self._info("Хранилище памяти не подключено.\n")
            return
        facts = self.store.all()
        if not facts:
            self._info("Память пуста.\n")
            return
        by_subject: dict[str, list[dict]] = {}
        for f in facts:
            by_subject.setdefault(f.get("subject", "?"), []).append(f)
        for subject, items in by_subject.items():
            title = "О тебе" if subject == "user" else subject
            print(f"{Color.YELLOW}{title}:{Color.RESET}")
            for f in items:
                mark = "" if f.get("source") == "stated" else f" {Color.DIM}(догадка){Color.RESET}"
                print(f"  • {f['fact']}{mark}")
        print()

    def _clear(self) -> None:
        if hasattr(self.agent, "dialog"):
            self.agent.dialog = []
        self._info("История диалога очищена. Долгая память сохранена.\n")

    # ---------- основной цикл ----------

    def run(self) -> None:
        self._greeting()
        commands = {"/help": self._help, "/memory": self._memory, "/clear": self._clear}

        while True:
            try:
                user_text = input(f"{Color.CYAN}{Color.BOLD}Вы:{Color.RESET} ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not user_text:
                continue
            if user_text.lower() in {"/exit", "exit", "выход"}:
                break
            if user_text.lower() in commands:
                commands[user_text.lower()]()
                continue

            print(f"{Color.DIM}думаю...{Color.RESET}", end="\r", flush=True)
            try:
                answer = self.agent.call(user_text)
            except KeyboardInterrupt:
                print(" " * 20, end="\r")
                self._info("Прервано.\n")
                continue
            except Exception as e:  # сеть, API, лимиты — не роняем чат
                print(" " * 20, end="\r")
                self._error(f"{type(e).__name__}: {e}")
                continue

            print(" " * 20, end="\r")  # затереть «думаю...»
            self._say(answer)

        self._info("До встречи!")