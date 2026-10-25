


class Dialog:
    def __init__(self, agent):
        self.agent = agent

    def run(self):
        while True:
            user_text = input()
            print(self.agent.call(user_text))