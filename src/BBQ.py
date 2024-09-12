from TestObject import TestObject
#import os


class BBQ(TestObject):
    """
    The class for the BBQ testcases. because of that this was the first example, no special action is nedded
    because the loadData function in the class TestObject can handle this all.
    """

    """
    @classmethod
    def loadData(bbq):
        class_name = "BBQ"
        path = "Testdata/" + class_name + "/data"
        fileList = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        for fileName in fileList:
            questions_path = 'Testdata/' + class_name + '/data/' + fileName
            if fileName.startswith('.'): # beacuase of hidden mac files
                continue
            with open(questions_path, 'r') as file:
                questionLines = [line.strip() for line in file]
            
            for question in questionLines:
                bbqObj = BBQ(fileName, question)
                bbqObj.agentCommand = "Answer the following statement."
"""