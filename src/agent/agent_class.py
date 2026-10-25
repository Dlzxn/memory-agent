from langchain_gigachat.chat_models import GigaChat
from langchain.agents import create_agent



class Agent:
    def __init__(
                self,
                 key: str,
                 model_name: str,
                 tools: list,
                 system_prompt: str,
                 context: list | None = None
                 ):
        self.key = key
        self.model = model_name
        self.sys_priompt = system_prompt
        self.dialog = [] if context is None else context
        self.tools = tools

        self.model = GigaChat(credentials=self.key, model=self.model, verify_ssl_certs=False)
        self.agent = None

        self._init_agent()

    def _init_agent(self):
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.sys_priompt
        )

    def call(self, input_text: str):
        self.dialog.append(
            {"role": "user", "content": input_text}
        )
        response = self.agent.invoke(
            {"messages": self.dialog}
        )
        self.dialog = response['messages']
        return self.dialog[-1].content


