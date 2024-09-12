from UserProxyAgent import UserProxyAgent
from TestObject     import TestObject
from Scenario       import Scenario, ScenarioResult

class ScenarioManager:
    """
    Class for a scenario manager who handles all scenarios.
    By instanciating a ScenarioManager it creates an empty list of scenarios
    """
    def __init__(self):
        """
        Initialise a list of scenarios
        """
        self.scenarios: list[Scenario] = []


    def ask_user(self, result):
        """
        If a result needs input from a user the user_proxy is used
        """
        user_proxy = UserProxyAgent()
        user_input = user_proxy.ask(result)
        # Handle user input further


    def processQuestion(self, testObject: TestObject, baseResulttext: str) -> list[ScenarioResult]:
        """
        All the given testObjects and questions shall be discussed.
        The Scenario results are added to the ResultObject. Therefore a ResultObject can have ScenarioResults of different scenarios.
        @param: testObject: this is just needed for having a reference to the original data
        @param: resultObject: ResultObject; The base result from the first single agent conversation
        """
        scenarioResults: list[ScenarioResult] = [] # just all the scenario results
        # go through all scenarios
        for scenario in self.scenarios:
            # print("Check testObject " + str(testObject.refId) + " with scenario '" + scenario.name + "'")
            # execute one scenario with the central assistant which creates the first answer
            result: ScenarioResult = scenario.execute(testObject, baseResulttext)
            if result == None:
                print("We have no result, perhaps because of an exception. So, we stop here.")
                break
            if scenario.requires_user_input:
                self.ask_user(result)
            scenarioResults.append(result) # add the result to the list

        return scenarioResults    # put the scenario results to the result object    
