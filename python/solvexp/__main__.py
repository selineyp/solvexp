
from python.solvexp.encodings.stable_marriage import StableMarriageEncoding
from python.solvexp.problems.stable_marriage import SMTI


if __name__ == "__main__":
    # read file 
    with open("input.txt", "r") as f:
        data = f.read()
    smti = SMTI.from_string(data)
    argFramework = StableMarriageEncoding.encode(smti)
    # solve
    stableSol = argFramework.computeStableExtension()
    print(stableSol)
    for pair in stableSol:
        print(pair)
        print('explanation for pair:', argFramework.getExplanation(pair))