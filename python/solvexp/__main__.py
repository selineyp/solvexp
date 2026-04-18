
from solvexp.src.encodings.stable_marriage import StableMarriageEncoding
from solvexp.src.problems.stable_marriage import SMTI


if __name__ == "__main__":
    import sys
    filename = sys.stdin.readline().strip() if not sys.stdin.isatty() else input("Enter file name: ")
    smti = SMTI.from_file(filename)
    argFramework = StableMarriageEncoding.encode(smti)
    # solve
    print('Computing a stable marriage...')
    stableExt = argFramework.computeStableExtension()
    for pair in stableExt:
        print(pair)
        print('Explanation for pair:', argFramework.getExplanation(stableExt, pair))