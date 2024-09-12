import json
import os
import importlib


class TestObject:
    """
    This class is used to harmonise different test data files and their different structures.
    Is this the case in the specialised subclasses the different elements must be overwritten.
    """
    # The attibutes of a single TestObject
    modul:               str = ""
    refFileName:         str = ""
    refId:               int = 0
    idName:              str = "example_id"
    agentCommand:        str = "Given is the following conversation: \n"
    statement:           str = ""
    statementName:       str = "context"
    question:            str = ""
    questionName:        str = "question"
    expectedAnswer1:     str = ""
    expectedAnswer1Name: str = "ans0"
    expectedAnswer2:     str = ""
    expectedAnswer2Name: str = "ans1"
    expectedAnswer3    : str = ""
    expectedAnswer3Name: str = "ans2"
    positiveResult     : int = 0
    positiveResultName : str = "label"

    def __init__(self):
        """
        When a new TestObject is instanciated it is added to the object list in the class TestObjects
        """
        TestObjects.testObjectList.append(self)


    def __init__(self, modul, refFileName, jsonString):
        """
        The main initialisation method with a filename and a jsonString with the content for a TestObject.
        We assume that we are dealing with Json objects.
        @param: refFileName: The name of the file with the test data. We want to know that for generating a result file for that.
        @param: jsonString: Each line of the file with the test cases should be a json object which is filled here.
        """
        self.modul           = modul
        self.refFileName     = refFileName
        try:
            jsonObject           = json.loads(str(jsonString))
            self.refId           = jsonObject.get(self.idName, None)
            self.statement       = jsonObject[self.statementName]
            self.question        = jsonObject[self.questionName]
            self.expectedAnswer1 = jsonObject[self.expectedAnswer1Name]
            self.expectedAnswer2 = jsonObject[self.expectedAnswer2Name]
            self.expectedAnswer3 = jsonObject[self.expectedAnswer3Name]
            self.positiveResult  = jsonObject[self.positiveResultName]
            TestObjects.testObjectList.append(self)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            # Handle JSON decode error (maybe set fields to None or provide defaults)
        except KeyError as e:
            print(f"Missing key in JSON data: {e}")
            # Handle missing keys (maybe set fields to None or provide defaults)


    def getQuestion(self) -> str:
        """
        @return: returns a string with the resulting question text
        """
        question = self.getQuestionWithoutPredefinedAnswers()
        # If there is a choice defined, use it
        if self.expectedAnswer1 and self.expectedAnswer2 and self.expectedAnswer3:
            question = question + " \nChoose one of the following answers:" + self.getPossibleAnswers()
        return question
    

    def getQuestionWithoutPredefinedAnswers(self) -> str:
        """
        @return: returns a string with the resulting question text
        """
        question = self.agentCommand + " '" + self.statement + "' \nAnswer the following question concerning this statement:\n'" + self.question + "'"
        return question
    

    def getPossibleAnswers(self) -> str:
        """
        @return: returns a string with all the expected values to use for asking for a concrete Answer.
        """
        answers: str = ""
        if self.expectedAnswer1 and self.expectedAnswer2 and self.expectedAnswer3:
            answers = "\n'0 = " + self.expectedAnswer1 + "', \n'1 = " + self.expectedAnswer2 +"', \n'2 = " + self.expectedAnswer3 + "'"
        return answers


class TestObjects:
    """
    Class for storing a list of test objects.
    """
    testObjectList: list[TestObject] = []

    @classmethod
    def loadData(cls, name: str) -> list[TestObject]:
        """
        This is the important class method to load data from a file into the list of TestObjects
        This is full generative.
        @param: name: str; The associated class is used dynamically with the given name.
        """
        class_name  = name
        module_name = name  # The name of the module in which the class is defined

        # modul and class have always the same name
        modul = importlib.import_module(module_name) # we load the class from the module
        classOfName = getattr(modul, class_name)     # with this we can get the class itself

        # Each class shall has its own directory of test data files
        path = "Testdata/" + class_name + "/data"
        try:
            fileList = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

            for fileName in fileList:
                questions_path = 'Testdata/' + class_name + '/data/' + fileName
                if fileName.startswith('.'): # beacuase of hidden mac files we jump over them
                    continue
                # from each file we read all the lines 
                with open(questions_path, 'r') as file:
                    questionLines = [line.strip() for line in file]
                
                # and generate TestObjects
                for question in questionLines:
                    classObj = classOfName(name, fileName, question)
                    classObj.agentCommand = "Answer the following statement:\n"

            return cls.testObjectList
        except Exception as e:
            return []
 

    @classmethod
    def loadIds4TestCases(cls, testName: str) -> list:
        """
        Method to load a list of IDs we have from previous tests and we want to choose for another test
        """
        # Step 1: Open the file
        values = []
        try:
            with open(testName, 'r') as file:
                # Step 2: Read all lines from the file
                lines = file.readlines()

            # Step 3: Process the lines to strip whitespace and convert to integers
            values = [int(line.strip()) for line in lines]
        except Exception as e:
            print("No Id file")
        return values

