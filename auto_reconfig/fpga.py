import os
import sys

def main(argv):

    os.system("modprobe catapult")
    os.system("fpgadiagnostics -dumphealth")
    if os.system("fpgadiagnostics -dumphealth | grep 'golden:0'") != 0:
        os.system("fpgadiagnostics -reconfigapp")
        os.system("fpgadiagnostics -dumphealth")

    # don’t forget to delete the service file!
    #os.system("rm /vol/data/persistent/tests/systemd/SoCFPGATestSvc.service”)
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
