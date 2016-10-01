from hsi import Panorama, ifstream

import sys
import numpy as np
from math import acos, cos, sin, atan, tan, pi, radians, sqrt

def main():
    try:
        ifs = ifstream(sys.argv[1])
    except IndexError:
        print("No arg given")
        return

    p = Panorama()
    p.readData(ifs)


    cpv = p.getCtrlPoints()

    picLinkNb = [0 for x in range(6)]
    distSum = 0
    nbPoints = 0

    for cp in cpv:
        picLinkNb[cp.image1Nr] += 1
        picLinkNb[cp.image2Nr] += 1

        nbPoints += 1

    minLinksNeeded = 4

    isStitchable = all(x > minLinksNeeded for x in picLinkNb)

    try:
        if sys.argv[2] == "csvData":
            print(isStitchable, nbPoints, sep=",",)
            exit()
    except IndexError:
        pass

    print("######### Stat #########")
    if not isStitchable:
        print("Panorama not stitchable")

    print("Number of CP: ", nbPoints)

    print("Picture links:",
            ' | '.join([
                "pic" + str(x) + ' ' + str(picLinkNb[x])
                for x in range(6)])
            )

    print("#######################")


if __name__ == "__main__":
    main()
