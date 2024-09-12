from TestObject import TestObject


class ResultObject:
    """
    Class for holding the results of scenario tests for a test object
    """
    test:             TestObject
    baseResulttext:   str                  = ""
    baseResultanswer: int
    hasFoundAnswer:   bool                 = False
    scenarioResults:  list                 = []

    def __init__(self):
        """
        When a new ResultObject is instanciated it is added to the object list in the class ResultObjects
        """
        ResultObjects.results.append(self)


    def __init__(self, test: TestObject, baseResulttext: str, baseResultanswer: int):
        """
        Create a new ResultObject and then add it to the object list in the class ResultObjects
        """
        self.test             = test
        self.baseResulttext   = baseResulttext
        self.baseResultanswer = baseResultanswer
        if test.positiveResult == baseResultanswer:
            self.hasFoundAnswer = True
        else: 
            self.hasFoundAnswer = False

        ResultObjects.results.append(self)
        

class ResultObjects:
    """
    Class for holding the list of ResultObject objects
    """
    results: list[ResultObject] = []


