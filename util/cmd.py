from typing import Union, Tuple, List
from threading import Thread
from subprocess import Popen, PIPE


def execute_sshpass_cmd():
    pass


def execute_cmd(
    cmd: Union[str, List[str], List[List[Union[str, List[str]]]]],
    initial_input: str = None,
    show_output=False,
    timeout: int = None,
) -> Tuple[str, str, int]:
    """
    Executes a command.
    If providing a list, the command is executed using Popen spawn syntax
    If the list contains a list, the command acts like piping.

    This does not replicate complex actions such as optional commands or
    piping stderr or writing to a file

    Returns stdout, stderr, return code
    """
    if isinstance(cmd, list):
        if not all(isinstance(item, str) for item in cmd):
            # Pipe!
            for i in len(cmd) - 1:
                new_cmd = cmd[i]
                (out, err, code) = execute_cmd(
                    new_cmd,
                    initial_input=initial_input,
                    show_output=show_output,
                    timeout=timeout,
                )
                if code != 0:
                    return (out, err, code)
                # Get output to feed into next command
                initial_input = out
            # Run the final command
            cmd = cmd[i + 1]

    use_shell = isinstance(cmd, str)
    p = Popen(
        cmd,
        shell=use_shell,
        text=True,
        stdout=PIPE,
        stderr=PIPE,
        stdin=PIPE,
    )
    stdout_result = []
    stderr_result = []

    def capture_result(stream, output_list: list, show_ouptut: bool):
        for line in iter(stream.readline, ""):
            if show_ouptut:
                print(line, end="")
            output_list.append(line)
        stream.close()

    stdout_thread = Thread(
        target=capture_result, args=(p.stdout, stdout_result, show_output)
    )
    stderr_thread = Thread(
        target=capture_result, args=(p.stderr, stderr_result, show_output)
    )

    stdout_thread.start()
    stderr_thread.start()

    if initial_input:
        p.stdin.write(initial_input)
        p.stdin.flush()
        p.stdin.close()

    p.wait(timeout=timeout)
    stdout_thread.join()
    stderr_thread.join()

    return ("".join(stdout_result), "".join(stderr_result), p.returncode)
