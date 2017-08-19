import sys
import io

class iostub:
    def stub_stdin(testcase_inst, inputs):
        stdin = sys.stdin

        def cleanup():
            sys.stdin = stdin

        testcase_inst.addCleanup(cleanup)
        sys.stdin = io.BytesIO(inputs)

    def stub_stdout(testcase_inst):
        stdout = sys.stdout

        def cleanup():
            sys.stdout = stdout

        testcase_inst.addCleanup(cleanup)
        sys.stdout = io.BytesIO()

    def stub_stdouts(testcase_inst):
        stderr = sys.stderr
        stdout = sys.stdout

        def cleanup():
            sys.stderr = stderr
            sys.stdout = stdout

        testcase_inst.addCleanup(cleanup)
        sys.stderr = io.BytesIO()
        sys.stdout = io.BytesIO()
