# -*- coding: utf-8 -*-

from subprocess import PIPE, Popen


def get_output(command):
    try:
        handle = Popen(
            command,
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            executable='/bin/bash'
        )
        stdout, stderr = handle.communicate()
        returncode = handle.returncode
        return stdout.strip(), stderr.strip(), returncode
    except ValueError:
        raise SystemExit
    except OSError:
        raise SystemExit
