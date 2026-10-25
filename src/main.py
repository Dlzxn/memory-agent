from dotenv import load_dotenv
load_dotenv()


from src.agent.agent_class import Agent
from src.func_call.functions import get_weather
from src.func_call.memory_func import MEMORY_TOOLS
from src.agent.dialog import Dialog

import os



if __name__ == "__main__":
    key = os.getenv('Authorization_Key')
    agent = Agent(
        key=key,
        model_name='GigaChat-3-Lightning',
        tools=[get_weather, *MEMORY_TOOLS],
        system_prompt="Ты-персональный агент по имени Джесси Пинкман. Функции возвращают ответ в формате json для того, что бы ты их обработал и корректно ответил пользователю. "
    )
    dialog = Dialog(agent)
    dialog.run()