from dexy.filters.pexpect_filters import KshInteractiveFilter
from ordereddict import OrderedDict
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.other import BashSessionLexer
import json
import os
import pexpect
import tempfile
import shutil

class KshTempdirInteractiveFilter(KshInteractiveFilter):
    """
    Runs ksh in a temporary directory, recording state of that directory.
    """
    ALIASES = ['shtmp']
    EXECUTABLE = "ksh -i -e"
    OUTPUT_EXTENSIONS = [".json"]

    def process_dict(self, input_dict):
        # Set up syntax highlighting
        html_formatter = HtmlFormatter()
        latex_formatter = LatexFormatter()
        lexer = BashSessionLexer()

        output_dict = OrderedDict()
        search_terms = self.prompt_search_terms()

        # Create a temporary directory where we will run our script.
        work_dir = tempfile.mkdtemp()

        for input_artifact in self.artifact.inputs().values():
            filename = os.path.join(work_dir, input_artifact.canonical_filename())
            if os.path.exists(input_artifact.filepath()):
                input_artifact.write_to_file(filename)
                self.log.debug("Populating temp dir for %s with %s" % (self.artifact.key, filename))
            else:
                self.log.warn("Skipping file %s for temp dir for %s, file does not exist (yet)" % (filename, self.artifact.key))

        env = self.setup_env()
        proc = pexpect.spawn(
                self.executable(),
                cwd=work_dir,
                env=env)
        timeout = self.setup_timeout()

        # Capture the initial prompt
        if self.INITIAL_PROMPT:
            proc.expect(self.INITIAL_PROMPT, timeout=timeout)
        elif self.PROMPT_REGEX:
            proc.expect(search_terms, timeout=timeout)
        else:
            proc.expect_exact(search_terms, timeout=timeout)

        start = proc.before + proc.after
        for section_key, section_text in input_dict.items():
            section_transcript = start
            start = ""

            lines = self.lines_for_section(section_text)
            for l in lines:
                section_transcript += start
                proc.send(l.rstrip() + "\n")
                if self.PROMPT_REGEX:
                    proc.expect(search_terms, timeout=timeout)
                else:
                    proc.expect_exact(search_terms, timeout=timeout)
                section_transcript += self.strip_newlines(proc.before)
                start = proc.after

            section_info = {}
            section_info['transcript'] = self.strip_trailing_prompts(section_transcript)
            section_info['transcript-html'] = highlight(section_info['transcript'], lexer, html_formatter)
            section_info['transcript-latex'] = highlight(section_info['transcript'], lexer, latex_formatter)

            section_info['files'] = {}
            for root, dirs, files in os.walk(work_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    local_path = os.path.relpath(filepath, work_dir)
                    with open(filepath, "r") as f:
                        contents = f.read()
                        try:
                            json.dumps(contents)
                            section_info['files'][local_path] = contents
                        except UnicodeDecodeError:
                            section_info['files'][local_path] = None

            # Save this section's output
            output_dict[section_key] = section_info

        try:
            proc.close()
        except pexpect.ExceptionPexpect:
            raise Exception("process %s may not have closed" % proc.pid)

        if proc.exitstatus:
            self.handle_subprocess_proc_return(proc.exitstatus, str(output_dict))

        for i in self.artifact.inputs().values():
            src = os.path.join(work_dir, i.filename())
            if i.virtual or i.additional and os.path.exists(src):
                shutil.copy(src, i.filepath())

        shutil.rmtree(work_dir)
        x = OrderedDict()
        x['1'] = json.dumps(output_dict)
        return x