#!/usr/bin/env python3
import validate_auto_reconfiguration

if __name__ == "__main__":
    sns = []
    line = input('Paste Arrays of Serial numbers (press enter twice if you copy from Test Monitor):\n').strip()
    while len(str(line)) != 0:
        sns.append(line.strip())
        line = input()
    for sn in sns:
        validate_auto_reconfiguration.main(sn)