from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
import pexpect

IREPLWrapper = replwrap.REPLWrapper

from subprocess import check_output
import os.path

import re
import signal

__version__ = '0.0.1'

version_pat = re.compile(r'version (\d+(\.\d+)+)')

vivado = "/opt/Xilinx/Vivado/2019.1/bin/vivado"

class VivadoKernel(Kernel):
    implementation = 'vivado_kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        m = version_pat.search(self.banner)
        return m.group(1)

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output([vivado, '-version']).decode('utf-8')
        return self._banner

    language_info = {'name': 'vivado',
                     'codemirror_mode': 'shell',
                     'mimetype': 'text/x-sh',
                     'file_extension': '.sh'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_vivado()

    def _start_vivado(self):
        # Signal handlers are inherited by forked processes, and we can't easily
        # reset it from the subprocess. Since kernelapp ignores SIGINT except in
        # message handlers, we need to temporarily reset the SIGINT handler here
        # so that vivado and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            # Note: the next few lines mirror functionality in the
            # vivado() function of pexpect/replwrap.py.  Look at the
            # source code there for comments and context for
            # understanding the code here.
            child = pexpect.spawn(vivado, ["-mode", "tcl", '-notrace'], # echo=False,
                                  encoding='utf-8', codec_errors='replace')

            # Using IREPLWrapper to get incremental output
            self.vivadowrapper = IREPLWrapper(
                child, u'Vivado% ', None, continuation_prompt=u'Vivado- ')
        finally:
            signal.signal(signal.SIGINT, sig)

    def process_output(self, output, code=''):
        if not self.silent:
            # vivado likes to echo your commands
            # Send standard output and likes to add a new line, in windows style
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        try:
            code = code.rstrip()
            output = self.vivadowrapper.run_command(code)
            # output = self.vivadowrapper.child.before
            self.process_output(output, code)
        except KeyboardInterrupt:
            self.vivadowrapper.child.sendintr()
            interrupted = True
            self.vivadowrapper._expect_prompt()
            output = self.vivadowrapper.child.before
            self.process_output(output)
        except EOF:
            output = self.vivadowrapper.child.before + 'Restarting Vivado'
            self._start_vivado()
            self.process_output(output)

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        try:
            # exitcode = int(self.vivadowrapper.run_command('echo $?').rstrip())
            exitcode = 0
        except Exception:
            exitcode = 1

        if exitcode:
            error_content = {
                'ename': '',
                'evalue': str(exitcode),
                'traceback': []
            }
            self.send_response(self.iopub_socket, 'error', error_content)

            error_content['execution_count'] = self.execution_count
            error_content['status'] = 'error'
            return error_content
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    def do_complete(self, code, cursor_pos):
        code = code[:cursor_pos]
        default = {'matches': [], 'cursor_start': 0,
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}

        if not code or code[-1] == ' ':
            return default

        tokens = code.replace(';', ' ').split()
        if not tokens:
            return default

        matches = []
        token = tokens[-1]
        start = cursor_pos - len(token)

        if token[0] == '$':
            # complete variables
            cmd = 'compgen -A arrayvar -A export -A variable %s' % token[1:] # strip leading $
            output = self.vivadowrapper.run_command(cmd).rstrip()
            completions = set(output.split())
            # append matches including leading $
            matches.extend(['$'+c for c in completions])
        else:
            # complete functions and builtins
            cmd = 'compgen -cdfa %s' % token
            output = self.vivadowrapper.run_command(cmd).rstrip()
            matches.extend(output.split())

        if not matches:
            return default
        matches = [m for m in matches if m.startswith(token)]

        return {'matches': sorted(matches), 'cursor_start': start,
                'cursor_end': cursor_pos, 'metadata': dict(),
                'status': 'ok'}
