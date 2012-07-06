
"""
Implementation of the command-line I{pyflakes} tool.
"""

import sys
import os
import _ast

checker = __import__('pyflakes.checker').checker


class Reporter(object):
    """
    Formats the results of pyflakes checks to users.
    """

    def __init__(self, errorStream):
        """
        Construct a L{Reporter}.

        @param errorStream: A file-like object where error output will be
            written to.  C{sys.stderr} is a good value.
        """
        self._stderr = errorStream


    def ioError(self, filename, msg):
        """
        There was an C{IOError} while reading C{filename}.
        """
        self._stderr.write("%s: %s\n" % (filename, msg.args[1]))


    def problemDecodingSource(self, filename):
        """
        There was a problem decoding the source code in C{filename}.
        """
        self._stderr.write(filename)
        self._stderr.write(': problem decoding source\n')


    def syntaxError(self, filename, msg, lineno, offset, line):
        """
        There was a syntax errror in C{filename}.

        @param filename: The path to the file with the syntax error.
        @param msg: An explanation of the syntax error.
        @param lineno: The line number where the syntax error occurred.
        @param offset: The column on which the syntax error occurred.
        @param line: The line of source code containing the syntax errr.
        """
        self._stderr.write('%s:%d: %s\n' % (filename, lineno, msg))
        self._stderr.write(line)
        self._stderr.write('\n')
        if offset is not None:
            self._stderr.write(" " * (offset + 1) + "^\n")



def check(codeString, filename, reporter=None):
    """
    Check the Python source given by C{codeString} for flakes.

    @param codeString: The Python source to check.
    @type codeString: C{str}

    @param filename: The name of the file the source came from, used to report
        errors.
    @type filename: C{str}

    @param reporter: A L{Reporter} instance, where errors and warnings will be
        reported.

    @return: The number of warnings emitted.
    @rtype: C{int}
    """
    if reporter is None:
        reporter = Reporter(sys.stderr)
    # First, compile into an AST and handle syntax errors.
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError, value:
        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        # If there's an encoding problem with the file, the text is None.
        if text is None:
            # Avoid using msg, since for the only known case, it contains a
            # bogus message that claims the encoding the file declared was
            # unknown.
            reporter.problemDecodingSource(filename)
        else:
            line = text.splitlines()[-1]
            if offset is not None:
                offset = offset - (len(text) - len(line))
            reporter.syntaxError(filename, msg, lineno, offset, line)
        return 1
    else:
        # Okay, it's syntactically valid.  Now check it.
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        for warning in w.messages:
            print warning
        return len(w.messages)


def checkPath(filename, reporter=None):
    """
    Check the given path, printing out any warnings detected.

    @param reporter: A L{Reporter} instance, where errors and warnings will be
        reported.

    @return: the number of warnings printed
    """
    if reporter is None:
        reporter = Reporter(sys.stderr)
    try:
        return check(file(filename, 'U').read() + '\n', filename, reporter)
    except IOError, msg:
        reporter.ioError(filename, msg)
        return 1


def main():
    warnings = 0
    args = sys.argv[1:]
    reporter = Reporter(sys.stderr)
    if args:
        for arg in args:
            if os.path.isdir(arg):
                for dirpath, dirnames, filenames in os.walk(arg):
                    for filename in filenames:
                        if filename.endswith('.py'):
                            warnings += checkPath(
                                os.path.join(dirpath, filename), reporter)
            else:
                warnings += checkPath(arg, reporter)
    else:
        warnings += check(sys.stdin.read(), '<stdin>')

    raise SystemExit(warnings > 0)
