# Based on metatoaster's answer to
# https://stackoverflow.com/questions/38861101/how-can-i-test-the-standard-input-and-standard-output-in-python-script-with-a-un
import sys
import io

class iostub:
    def stub_stdin(testcase_inst, inputs, ioclass=io.StringIO):
        stdin = sys.stdin

        def cleanup():
            sys.stdin = stdin

        testcase_inst.addCleanup(cleanup)
        sys.stdin = ioclass(inputs)
        if ioclass == io.BytesIO:
            # Fake 'buffer' variable
            sys.stdin.buffer = sys.stdin

    def stub_stdout(testcase_inst, ioclass=io.StringIO):
        stdout = sys.stdout

        def cleanup():
            sys.stdout = stdout

        testcase_inst.addCleanup(cleanup)
        sys.stdout = ioclass()
        if ioclass == io.BytesIO:
            # Fake 'buffer' variable
            sys.stdout.buffer = sys.stdout

    def stub_stdouts(testcase_inst, ioclass=io.StringIO):
        stderr = sys.stderr
        stdout = sys.stdout

        def cleanup():
            sys.stderr = stderr
            sys.stdout = stdout

        testcase_inst.addCleanup(cleanup)
        sys.stderr = ioclass()
        sys.stdout = ioclass()
        if ioclass == io.BytesIO:
            # Fake 'buffer' variable
            sys.stdout.buffer = sys.stdout
            sys.stderr.buffer = sys.stderr
