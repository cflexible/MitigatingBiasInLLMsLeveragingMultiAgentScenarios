# Mitigating Bias in Large Language Models Leveraging Multi-Agent Scenarios

## Short description
This small programs are for running test to find out if additional agents using LLMs can improve the answer quality of biased based questions. Or in other words if it is possible to mitigate bias by checking responses from LLMs about bias and let the LLMs correct theirs answers by using the feedback.

## Installation
### Prerequisites
- Python 3.12.3
- Libraries: `csv`, `json`, `os`, `sys`, `numpy`, `random`, `datetime`, `shutil`, `typing`, `autogen`

### Installationsanleitung
1. Library installation
    Install the named libraries in the normal way
2. Create the following subfolders
    /coding
    /logs
    /Results
    /StatisticResults
    /Testdata
    optional /Testdata/BBQ/data if you like to use the BBQ dataset
3. If you want to use ChatGPT as a LLM, set you API key in the file OAI_CONFIG_LIST
4. Set the parameter in the file Configvalues.py like:
    lLMVersion            = "<THE NAME OF THE LLM AS IT IS IN OAI_CONFIG_LIST>"
    numberOfTestsToChoose = 100
    cleanHistory: bool    = True
5. Set values in Evaluator.py
    Set the name of the test at the end of the file. This must be the same as the first subfolder of /Testdata
        testname:       str       = "BBQ"
   Set the name of the bias test:
        idFileName = "<NAME OF BIAS TYPE>Ids" + str(Konfigvalues.numberOfTestsToChoose) + ".txt"
6. Put a file to test into the /Testdata/<TESTNAME>/data with the test data as .jsonl file. For examples see at https://github.com/i-gallegos/Fair-LLM-Benchmark/tree/main/BBQ
7. Run the Evaluator

### More informations
More informations can be found in the master thesis with the name "Mitigating Bias in Large Language Models Leveraging Multi-Agent Scenarios"


Authors:
    Jens Luenstedt