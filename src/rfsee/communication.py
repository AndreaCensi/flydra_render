import sys
from cjson import decode, encode

def exit_with_error(string, code= -1):
    """ Writes error string to stderr, JSON to stdout, exits with code"""
    sys.stderr.write(string)
    sys.stderr.write("\n")
    sys.stderr.flush();
    sys.stdout.write(encode({'ok': 0, 'status': string}))
    sys.stdout.write("\n")
    sys.stdout.flush();
    sys.exit(code)
    
def positive_answer(answer={}, status=""):
    answer['ok'] = 1;
    answer['status'] = status;
    sys.stdout.write(encode(answer))
    sys.stdout.write("\n")
    sys.stdout.flush();
