from dexy.handler import DexyHandler
import shutil

class PdfFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']

    def process(self):
        self.artifact.auto_write_artifact = False
        shutil.copyfile(self.artifact.previous_artifact_filename, self.artifact.filename())

class ConvertBashFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*", "*"]
    OUTPUT_EXTENSIONS = [".sh"]
    ALIASES = ['b', 'forcebash']

class ConvertTextFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['ct']

class TextFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['t', 'forcetext']

class LatexFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class HtmlFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class JsonFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']

class CleanNonPrinting(DexyHandler):
    ALIASES = ['cl']

    def process_text(self, input_text):
        return input_text.replace("\b", "")

