import datetime

class Konfigvalues:
    """
    Class to hold the global lLMVersion the system shall use.
    And to hold a value of a timestamp which is used for all files to know which files belong together.
    """
    lLMVersion            = "carterprince/google-gemma-2-27b-it-ortho-Q4_K_S-GGUF"
    numberOfTestsToChoose = 100
    cleanHistory: bool    = True

    now: str = ""

    @classmethod
    def getNowTimestamp(cls) -> str:
        """
        Class method to get a string of the current time stamp and to save it into the global variable
        """
        if len(Konfigvalues.now) == 0:
            Konfigvalues.now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        return Konfigvalues.now

    @classmethod
    def getllM(cls) -> str:
        """
        Returns the name of the used LLM without a problematic /
        """
        return Konfigvalues.lLMVersion.replace("/", "-")