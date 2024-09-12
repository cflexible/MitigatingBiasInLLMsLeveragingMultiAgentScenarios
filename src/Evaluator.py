import csv
import json
import os
import sys
import numpy as np
import random
import datetime
import shutil
import copy

from typing  import List
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

from TestObject       import TestObjects
from TestObject       import TestObject
from Configvalues     import Konfigvalues
from ScenarioManager  import ScenarioManager
from Scenario         import Scenario
from ResultObject     import ResultObject
from ResultObject     import ResultObjects


class Evaluator:
    """
    Main class of the experimental setup. The central elements are created in this class, 
    such as the individual agents that are interconnected in scenarios. It starts with the 
    user proxy and the central agent to be supported. Then 3 different agent pools are 
    defined, each of which forms a chat group and which together discuss the result of the 
    central agent. At the end, the central agent is asked to deliver a revised version of 
    its original statement.
    """

    def __init__(self, configFile):
        """
        Initialize the Evaluator class.
        The central agents for simulating a user input (user proxy) and a central assistant agent are defined in the init method. 
        The agents could use different LLMs (but we don't use that) whose configuration is read from the OAI_CONFIG_LIST file.
        @param: config_file: Name of configuration file
        """
        # Part of global attributes
        self.chatLlmConfig: dict = {}
        self.maxAutoReply:  int  = 0
        self.userProxy:     UserProxyAgent = None
        self.userAssistant: AssistantAgent = None

        """We define some llm_configs to use different LLMs"""
        filterDict = {"model": [Konfigvalues.lLMVersion]}
        configList = config_list_from_json(env_or_file=configFile, filter_dict=filterDict)

        userLlmConfig = {
            "config_list": configList,
#            "request_timeout": 120,
            "seed": 1,
            "temperature": 0 # Later to change for random results
        }
        
        self.chatLlmConfig = {
            "config_list": configList,
#            "request_timeout": 120,
            "seed": 1,
            "temperature": 0 # Later to change for random results
        }
        
        filterDict = {"model": [Konfigvalues.lLMVersion]}
        configList = config_list_from_json(env_or_file = configFile, filter_dict = filterDict)

        centralLlmConfig = {
            "config_list": configList,
#            "request_timeout": 120,
            "seed": 1,
            "temperature": 0 # Later to change for random results
        }
        """End of defining special llm configs"""
        
        self.maxAutoReply: int = 1


        """We define some Agents"""
        # Create user proxy agent
        self.userProxy = UserProxyAgent(
            name="userProxy",
            code_execution_config      = {"work_dir": "coding",
                                          "use_docker": False},
            human_input_mode           = "NEVER",
            max_consecutive_auto_reply = self.maxAutoReply,
            is_termination_msg         = lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            llm_config                 = userLlmConfig,
            system_message             = "Your task is to ask an assistant and after getting an answer, stop the conversation without any replies.",
            )


        # We create our first assistant which shall answer the question without any help
        def continueAssistantConversation(recipient, messages, sender, config):
            """
            For automatic continuing the conversation between the user proxy agent and another agents
            """
            if len(messages) > 0:
                lastMessage = messages[(len(messages) - 1)]['content']
                # print("Lastmessage executer Assistant: " + lastMessage)
                if "CONTINUE" in lastMessage or "TERMINATE" in lastMessage or "successfully completed" in lastMessage:
                    return True, "Conversation ended successfully."
            return False, None  # required to ensure the agent communication flow continues

        self.userAssistant = AssistantAgent(name                       = "userAssistant", 
                                            system_message             = "Your task is to answer the user's questions.",
                                            llm_config                 = centralLlmConfig, 
                                            max_consecutive_auto_reply = self.maxAutoReply,
                                            human_input_mode           = "NEVER",
                                            )
        
        self.userAssistant.register_reply(
            [UserProxyAgent, None],
            reply_func = continueAssistantConversation,
            config = {"callback": None},
        )
        # END of UserAssistant definition
        

    def loadScenarios(self, userProxy) -> List[Scenario]:
        """
        Load all scenarios and their correspondent agent definitions from the file 'Scenariodefinitions.json'.
        @param: userProxy: UserProxyAgent; to put into the scenarios to use as a central user proxy
        @return: A list of Scenario objects
        """
        with open('Scenariodefinitions.json') as f:
            definitions = json.load(f)

            scenarios = []
            for definition in definitions['Scenarios']:
                scenarioName     = definition['name']
                executerMessage  = definition['executerMessage']
                agentDefinitions = definition['agents']
                agents = []
                for agentDefinition in agentDefinitions:
                    agentName     = agentDefinition['name']
                    systemMessage = agentDefinition['systemMessage']
                    agent         = self.createAgent(name = agentName, message = systemMessage)
                    agents.append(agent)
                scenario = self.createScenario(scenarioName, executerMessage, agents, userProxy)
                scenarios.append(scenario)
            return scenarios
        

    def createScenario(self, name: str, executerMessage: str, agents:List[AssistantAgent], userProxy: UserProxyAgent) -> Scenario:
        """
        Create one scenario object with a list of agents and set the user proxy
        @param: name: str; The name of the scenario
        @param: executerMessage: str; To define the executer agent, which is used from the scenario, its role and what it shall do
        @param: agents: List[AssistantAgent]; 
        @param: userProxy: UserProxyAgent; The user proxy which shall be used by the scenario
        @return: Scenario; Returns a full defined Scenario object
        """
        scenario = Scenario(name            = name,
                            executerMessage = executerMessage,
                            agents          = agents)
        scenario.setUserProxy(userProxy)
        return scenario
    

    def createAgent(self, name, message) -> AssistantAgent:
        """
        Scenario agents are created using the createAgent method. The method is used to 
        simplify and centralise the configuration of the agents.
        @param: name: The name of the agent
        @param: message: The configuration message, so the agent knows which role it has.
        @return: An AssistantAgent object
        """
#        message =  + " Check if your expectations are covered and ask the questions."
#        message = message + " Do not show appreciation in your responses, say only what is necessary. If 'Thank you' or 'You\'re welcome' are said in the conversation, then say TERMINATE "
#        message = message + "to indicate the conversation is finished and this is your last message."

        assistant =  AssistantAgent(name                 = name, 
                              llm_config                 = self.chatLlmConfig,
                              system_message             = message,
                              max_consecutive_auto_reply = self.maxAutoReply,
                              is_termination_msg         = lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                              human_input_mode           = "NEVER",
                              )
        return assistant
    

    def readTestdataFor(self, name):
        """
        This method reads the file names from the directory that belong to the specified test case.
        @param: name: The name of the test case, e.g.: BBQ
        @return: a list of file names
        """
        path = "Testdata/" + name + "/data"
        onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        return onlyfiles


    def readQuestions(self, questionsFile: str):
        """
        Reads questions from the provided file.
        @param: a name of a file from which the questions are read into a line array
        :return: A list of questions (lines from the file).
        """
        with open(questionsFile, 'r') as file:
            return [line.strip() for line in file]


    def getScenarioManager(self, scenarios: List[Scenario]) -> ScenarioManager:
        # Create the conversable agent and give him the wished scenarios
        scenarioManager = ScenarioManager()
        scenarioManager.scenarios = scenarios
        return scenarioManager


    def evaluateQuestions(self, testname: str):
        """
        First a conversable agent is created to handle different scenarios. Then the pre defined scenarios
        are added to the conversable agent.
        We would like to use different Tests. So with the function loadData, data is loaded for a special testcase.
        Every testcase has its own class inherited of TestObject for special functions but it also is possible that
        the loadData function of TestObject is enough.
        By loadData the class TestObjects has a list of test objects and in the third part of the method, for all 
        test objects a test with the scenarios is initiated.
        For every TestObject a new result file is created.
        @param: testname: str ; the name of a folder where there are different test files
        """
        scenarios: List[Scenario] = evaluator.loadScenarios(evaluator.userProxy)

        # Create the scenario manager instance and give him the wished scenarios
        scenarioManager = self.getScenarioManager(scenarios)

        TestObjects.loadData(testname)
        fullQuestionList = TestObjects.testObjectList

        idFileName = "NationalityIds" + str(Konfigvalues.numberOfTestsToChoose) + ".txt"
        testIds = TestObjects.loadIds4TestCases(idFileName)
        if testIds == []:
            randomQuestionList = sorted(random.sample(fullQuestionList, min(len(fullQuestionList), Konfigvalues.numberOfTestsToChoose)), key=lambda obj: obj.refId)
        else:
            randomQuestionList = [obj for obj in fullQuestionList if obj.refId in testIds]

        # We go through all TestObjects
        testCounter = 0
        for testObject in randomQuestionList:
            testCounter = testCounter + 1
            print("\nTTTTTTTTTTTTTTTTTT\nStart of TEST: " + str(testCounter) + " with the id " + str(testObject.refId))
            # We get the main question from the testObject which includes a statement and a question about it
            question = testObject.getQuestion() + "\nPlease only output the correct answer. Do not add any additional explanations. Stop the conversation after your answer."
            # print("With full question: " + question)

            # Our first result is from the user assistant which gives the answer without any help
            try:
                if Konfigvalues.cleanHistory:
                    self.userProxy.clear_history()
                    self.userAssistant.clear_history()
                baseResult = self.userProxy.initiate_chat(self.userAssistant, 
                                        message        = question,
                                        summary_method = "last_msg")
            except Exception as e:
                print("We have an exception, perhaps because of running out of payment.")
                break

            # We get some results and we check if it is possible to find one of the possible answers in it
            summary = Scenario.summaryFromChatHistory(baseResult, 'user')
            resultNo = Scenario.resultNoFromChatHistory(summary, testObject, 'user')

            foundAnswser = Scenario.foundResultFromChatHistory(baseResult, testObject, 'user')

            # With all this information, a result object is created
            # When a ResultObject is created it is added to the ResultObjects global result list
            testResult = ResultObject(testObject, summary, resultNo)
            baseResultAnswer = testResult.baseResulttext
            if len(foundAnswser) > 0:
                baseResultAnswer = foundAnswser
            # We have our base result and now the results from the defined scenarios are collected
            print("We have a BASE RESULT for " + str(testObject.refId) + " with: '" + baseResultAnswer + "' which means that we found the correct answer = " + str(Scenario.hasFoundExpectedAnswer(resultNo, testObject)))

            # here we run all the other test scenarios
            testResult.scenarioResults = scenarioManager.processQuestion(testObject, baseResultAnswer)
            
            print("END of TEST " + str(testCounter) + " with the id " + str(testObject.refId) + "\n")
            print(str(int(testCounter * 100 / len(randomQuestionList))) + "% " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


    def writeCountResults(self, resultCounter, countTestresults: int, fileName: str):
        """
        Get the result counter values and calculate the statistic values. Write them into the csv file at the end
        @param: resultCounter: array[][][], a 3d array with count results
        @param: fileName: str, the name of the file
        """
        # Now we can write the count results and do some calculations
        resultRow0 = ['Average precision']+['']+['']+['']+['']
        resultRow1 = ['Average recall']+['']+['']+['']+['']
        resultRow2 = ['F-Score']+['']+['']+['']+['']

        # a loop through all tests
        for i in (range(int(resultCounter.size / 9))): # every scenario has 9 value and its own column
            column = i
            sumActualA    = resultCounter[column][0][0] + resultCounter[column][1][0] + resultCounter[column][2][0]
            sumPredictedA = resultCounter[column][0][0] + resultCounter[column][0][1] + resultCounter[column][0][2]
            precisionA    = resultCounter[column][0][0] / max(1, sumActualA)
            recallA       = resultCounter[column][0][0] / max(1, sumPredictedA)
            sumActualB    = resultCounter[column][0][1] + resultCounter[column][1][1] + resultCounter[column][2][1]
            sumPredictedB = resultCounter[column][1][0] + resultCounter[column][1][1] + resultCounter[column][1][2]
            precisionB    = resultCounter[column][1][1] / max(1, sumActualB)
            recallB       = resultCounter[column][1][1] / max(1, sumPredictedB)
            sumActualC    = resultCounter[column][0][2] + resultCounter[column][1][2] + resultCounter[column][2][2]
            sumPredictedC = resultCounter[column][2][0] + resultCounter[column][2][1] + resultCounter[column][2][2]
            precisionC    = resultCounter[column][2][2] / max(1, sumActualC)
            recallC       = resultCounter[column][2][2] / max(1, sumPredictedC)

            averagePrecision = (precisionA * sumPredictedA + precisionB * sumPredictedB + precisionC * sumPredictedC) / countTestresults
            averageRecall    = (recallA * sumPredictedA + recallB * sumPredictedB + recallC * sumPredictedC) / countTestresults
            f_score  = 2 * averagePrecision * averageRecall / (averagePrecision + averageRecall)
            if i > 0: # For the scenarios we jump 3 columns
                resultRow0 = resultRow0 + ['']+['']+['']
                resultRow1 = resultRow1 + ['']+['']+['']
                resultRow2 = resultRow2 + ['']+['']+['']
            resultRow0 = resultRow0 + [averagePrecision]
            resultRow1 = resultRow1 + [averageRecall]
            resultRow2 = resultRow2 + [f_score]
        
        self.writeLineToCsv(fileName, resultRow0)
        self.writeLineToCsv(fileName, resultRow1)
        self.writeLineToCsv(fileName, resultRow2)


    def writeResults(self, testResults: List):
        """
        Take the test results (a list), write the to a csv file and count the result values
        @param: testResults: List, the list of all test results. They contain the scenario results
        """
        # we have a 3 dimensional array to hold the result counter while the first value is for the result type 0 = base, 1 = scenario 1 and so on
        if len(testResults) == 0:
            print("NO RESULTS TO WRITE")
            return
        
        # there are three possible answer values and three possible expected answers and every result has 9 values
        maxExistingScenarioResults = 0
        for result in testResults:
            maxExistingScenarioResults = max(maxExistingScenarioResults, len(result.scenarioResults))
        resultCounter = np.zeros(((maxExistingScenarioResults + 1), 3, 3))

        oldFileName: str = ""
        fileName:    str = ""
        for testResult in testResults:
            fileName = "Results/" + testResult.test.modul + "_" + testResult.test.refFileName.partition('.')[0] + '_results_' + Konfigvalues.getNowTimestamp() + '-' + Konfigvalues.getllM() + '.csv'
            if len(oldFileName) > 0 and oldFileName != fileName:
                self.writeCountResults(resultCounter, oldFileName)
                resultCounter = np.zeros(((len(testResults[0].scenarioResults) + 1), 3, 3)) # reset of the result counter
                
            headers = ['Reference Id'] + ['Start question'] + ['Expected result'] + ['Initial result text']+ ['Initial answerNo'] + ['Initial expectation fulfilled']
            for i in range(len(testResult.scenarioResults)):
                headers.append(f'Scenario {i+1} expert answer')
                headers.append(f'Scenario {i+1} answer text')
                headers.append(f'Scenario {i+1} answer no')
                headers.append(f'Scenario {i+1} expectation fulfilled')

            if not os.path.exists(fileName):
                self.writeLineToCsv(fileName, headers)

            # Build a matrix in which the results are count
            # First the base results of the test is used
            if testResult.baseResultanswer == 0 and testResult.test.positiveResult == 0:
                resultCounter[0][0][0] += 1
            elif testResult.baseResultanswer == 1 and testResult.test.positiveResult == 0:
                resultCounter[0][1][0] += 1
            elif testResult.baseResultanswer == 2 and testResult.test.positiveResult == 0:
                resultCounter[0][2][0] += 1
            elif testResult.baseResultanswer == 0 and testResult.test.positiveResult == 1:
                resultCounter[0][0][1] += 1
            elif testResult.baseResultanswer == 1 and testResult.test.positiveResult == 1:
                resultCounter[0][1][1] += 1
            elif testResult.baseResultanswer == 2 and testResult.test.positiveResult == 1:
                resultCounter[0][2][1] += 1
            elif testResult.baseResultanswer == 0 and testResult.test.positiveResult == 2:
                resultCounter[0][0][2] += 1
            elif testResult.baseResultanswer == 1 and testResult.test.positiveResult == 2:
                resultCounter[0][1][2] += 1
            elif testResult.baseResultanswer == 2 and testResult.test.positiveResult == 2:
                resultCounter[0][2][2] += 1

            row: list[str] = []
            row.append(testResult.test.refId)
            row.append(testResult.test.getQuestion())
            row.append(testResult.test.positiveResult)
            row.append(testResult.baseResulttext)
            row.append(testResult.baseResultanswer)
            row.append(testResult.hasFoundAnswer)
            # Now from all scenario results the matrix is filled
            for i in range(len(testResult.scenarioResults)):
                row.append(testResult.scenarioResults[i].expertAnswer)
                row.append(testResult.scenarioResults[i].resultText)
                row.append(testResult.scenarioResults[i].resultValue)
                row.append(testResult.scenarioResults[i].hasFoundAnswer)
                # We collect information for later calculation
                # We need to add +1 to every result because 0 is the base result
                if testResult.scenarioResults[i].resultValue == 0 and testResult.test.positiveResult == 0:
                    resultCounter[i+1][0][0] += 1
                elif testResult.scenarioResults[i].resultValue == 1 and testResult.test.positiveResult == 0:
                    resultCounter[i+1][1][0] += 1
                elif testResult.scenarioResults[i].resultValue == 2 and testResult.test.positiveResult == 0:
                    resultCounter[i+1][2][0] += 1
                elif testResult.scenarioResults[i].resultValue == 0 and testResult.test.positiveResult == 1:
                    resultCounter[i+1][0][1] += 1
                elif testResult.scenarioResults[i].resultValue == 1 and testResult.test.positiveResult == 1:
                    resultCounter[i+1][1][1] += 1
                elif testResult.scenarioResults[i].resultValue == 2 and testResult.test.positiveResult == 1:
                    resultCounter[i+1][2][1] += 1
                elif testResult.scenarioResults[i].resultValue == 0 and testResult.test.positiveResult == 2:
                    resultCounter[i+1][0][2] += 1
                elif testResult.scenarioResults[i].resultValue == 1 and testResult.test.positiveResult == 2:
                    resultCounter[i+1][1][2] += 1
                elif testResult.scenarioResults[i].resultValue == 2 and testResult.test.positiveResult == 2:
                    resultCounter[i+1][2][2] += 1

            self.writeLineToCsv(fileName, row)

        # there is now a sum of all answer possibilities of all tests
        self.writeCountResults(resultCounter, len(testResults), fileName)


    def writeLineToCsv(self, fileName: str, row:List[str]):
        """
        Get a list of string values and write them to a given csv file
        @param: fileName: str, the name of the file
        @param: row: List[str]; A list which is written as a csv row
        """
        if os.path.exists(fileName):
            mode = 'a'
        else:
            mode = 'w'

        with open(fileName, mode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerow(row)




# MAIN:
try:
    shutil.rmtree(".cache")
except  Exception as e:
    print("No cache to delete")

file_path = "logs/evaluator_run_" + Konfigvalues.getllM() + "_" + Konfigvalues.getNowTimestamp() + ".log"
sys.stdout = open(file_path, "w")

# One test case, might be more later
testname:       str       = "BBQ"

configFilePath: str       = 'OAI_CONFIG_LIST'
evaluator:      Evaluator = Evaluator(configFile = configFilePath)

# Evaluate the questions and store the results in a CSV.
evaluator.evaluateQuestions(testname)
evaluator.writeResults(ResultObjects.results)