from dexy.reporter import Reporter
from dexy.doc import Doc
import subprocess

class GraphReporter(Reporter):
    ALIASES = ['graph', 'dot']

    @classmethod
    def write_graph_to_dotfile(klass, wrapper, dotfile):
        with open(dotfile, "w") as f:
            f.write(wrapper.graph)

    @classmethod
    def render_dotfile_to_png(klass, dotfile, pngfile):
        command = "dot %s -Tpng -o%s" % (dotfile, pngfile)
        proc = subprocess.Popen(
                   command,
                   shell=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT
               )
        proc.communicate()

    def run(self, wrapper):
        dotfile = os.path.join(wrapper.log_dir, 'dexygraph.dot')
        pngfile = os.path.join(wrapper.log_dir, 'dexygraph.png')

        self.write_graph_to_dotfile(self.wrapper, dotfile)
        self.render_dotfile_to_image(dotfile, pngfile)