import sys


def log(*args, level="INFO"):
    print(f'CEDDY | {level} : {" ".join(args)}')
    if level == "CRIT":
        sys.exit(1)
