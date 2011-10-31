from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict
import os
import pexpect
import re
import shutil
import time

class ProcessLinewiseInteractiveFilter(DexyFilter):
    """
    Intended for use with interactive processes, such as python interpreter,
    where your goal is to have a session transcript divided into same sections
    as input. Sends input line-by-line.
    """
    PROMPT = ['>>>', '...'] # Python uses >>> prompt normally and ... when in multi-line structures like loops
    TRIM_PROMPT = '>>>'
    LINE_ENDING = "\r\n"
    IGNORE_ERRORS = False # Allow overriding default per-filter.
    SAVE_VARS_TO_JSON_CMD = None
    ALIASES = ['processlinewiseinteractivefilter']

    def process_dict(self, input_dict):
        output_dict = OrderedDict()

        if self.artifact.args.has_key('timeout'):
            timeout = self.artifact.args['timeout']
            self.log.info("using custom timeout %s for %s" % (timeout, self.artifact.key))
        else:
            timeout = None
        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
            self.log.info("adding to env: %s" % self.artifact.args['env'])
        else:
            env = None

        proc = pexpect.spawn(self.EXECUTABLE, cwd=self.artifact.artifacts_dir, env=env)
        proc.expect_exact(self.PROMPT, timeout=timeout)
        start = (proc.before + proc.after)

        search_terms = ["%s%s" % (self.LINE_ENDING, p) for p in self.PROMPT]

        for k, s in input_dict.items():
            # TODO Should stop processing if an error is raised.
            section_transcript = start
            start = ""
            for l in (s+"\r\n").splitlines():
                section_transcript += start
                start = ""
                proc.sendline(l)
                proc.expect_exact(search_terms, timeout=timeout)
                section_transcript += proc.before
                start = proc.after

            # Strip blank lines/trailing prompts at end of section
            lines = section_transcript.split(self.LINE_ENDING)
            while len(lines) > 0 and re.match("^\s*(%s)\s*$|^\s*$" % self.TRIM_PROMPT, lines[-1]):
                lines = lines[0:-1]

#            output_dict[k] = ''.join([c for c in self.LINE_ENDING.join(lines) if ord(c) > 31 or ord(c) in [9, 10]])
            output_dict[k] = self.LINE_ENDING.join(lines)

        record_vars = self.artifact.args.has_key('record-vars') and self.artifact.args['record-vars']
        if record_vars:
            if not self.SAVE_VARS_TO_JSON_CMD:
                raise Exception("Can't record vars since SAVE_VARS_TO_JSON_CMD not set.")
            artifact = self.artifact.add_additional_artifact(self.artifact.key + "-vars", 'json')
            self.log.debug("Added additional artifact %s (hashstring %s) to store variables" % (artifact.key, artifact.hashstring))
            cmd = self.SAVE_VARS_TO_JSON_CMD % artifact.filename()

            section_transcript = start
            start = ""
            for l in cmd.splitlines():
                section_transcript += start
                start = ""
                proc.sendline(l)
                proc.expect_exact(search_terms, timeout=timeout)
                section_transcript += proc.before
                start = proc.after

            # This adds the code processing to the section transcript for display or debugging.
            output_dict['dexy--save-vars'] = section_transcript

        try:
            proc.close()
        except pexpect.ExceptionPexpect:
            print "process %s may not have closed" % proc.pid

        if proc.exitstatus is not None and proc.exitstatus != 0:
            if not (self.IGNORE_ERRORS or self.artifact.args.ignore_errors):
                raise Exception("""proc returned nonzero status code! if you don't
want dexy to raise errors on failed scripts then pass the --ignore-errors option""")
        return output_dict

class PythonLinewiseInteractiveFilter(ProcessLinewiseInteractiveFilter):
    ALIASES = ['pycon']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".pycon"]
    TAGS = ['python', 'interpreter', 'language']
    VERSION = 'python --version'

    SAVE_VARS_TO_JSON_CMD = """
import json
dexy__vars_file = open("%s", "w")
dexy__x = {}
for dexy__k, dexy__v in locals().items():
    dexy__x[dexy__k] = str(dexy__v)

json.dump(dexy__x, dexy__vars_file)
dexy__vars_file.close()
"""

class RLinewiseInteractiveFilter(ProcessLinewiseInteractiveFilter):
    """
    Runs R
    """
    ALIASES = ['r', 'rint']
    EXECUTABLE = "R --quiet --vanilla"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = ['.Rout']
    PROMPT = [">", "+"]
    TAGS = ['r', 'interpreter', 'language']
    TRIM_PROMPT = ">"
    VERSION = "R --version"
    SAVE_VARS_TO_JSON_CMD = """
if ("rjson" %%in%% installed.packages()) {
    library(rjson)
    dexy__json_file <- file("%s", "w")
    writeLines(toJSON(as.list(environment())), dexy__json_file)
    close(dexy__json_file)
} else {
   cat("Can't automatically save environment to JSON since rjson package not installed.")
}
"""

class RhinoInteractiveFilter(ProcessLinewiseInteractiveFilter):
    """
    Runs rhino JavaScript interpeter.
    """
    EXECUTABLE = "rhino"
    INPUT_EXTENSIONS = [".js"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jsint', 'rhino']
    PROMPT = "js> "

class ClojureInteractiveFilter(ProcessLinewiseInteractiveFilter):
    """
    Runs clojure.
    """
    EXECUTABLE = None
    EXECUTABLES = ['clojure', 'clj -r', 'java clojure.main']
    INPUT_EXTENSIONS = [".clj"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['clj', 'cljint']
    PROMPT = "user=> "

class ProcessTimingFilter(DexyFilter):
    """
    Runs python code N times and reports timings.
    """
    EXECUTABLE = 'python'
    VERSION = 'python --version'
    N = 10
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".times"]
    ALIASES = ['timing', 'pytime']

    def process(self):
        self.artifact.generate_workfile()
        times = []
        for i in xrange(self.N):
            start = time.time()
            pexpect.run("%s %s" % (self.EXECUTABLE, self.artifact.work_filename()))
            times.append("%s" % (time.time() - start))
        self.artifact.data_dict['1'] = "\n".join(times)

