def get_sns():
    sns = []
    line = input(
        "Paste list of serial numbers (when done, enter a blank line):\n"
    ).strip()
    try:
        while len(str(line)) != 0:
            sns.append(line.strip())
            line = input()
    except:
        pass
    return sns


def get_cmd():
    cmd = input("Input the individual cmd (default: set system reset):")
    if len(cmd) == 0:
        cmd = "set system reset"
    return cmd
