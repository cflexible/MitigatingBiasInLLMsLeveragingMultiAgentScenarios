from autogen import UserProxyAgent


class UserProxyAgent(UserProxyAgent):
    def __init__(self):
        super(UserProxyAgent, self).__init__()

    def ask(self, prompt):
        return input(prompt)
