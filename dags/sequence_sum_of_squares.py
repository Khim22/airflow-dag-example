from typing import List


def returnListOfSums(endNum: int) -> List[int]:
    return returnListOfSums(0, endNum)

def returnListOfSums(startNum:int, endNum: int) -> List[int]:
    ans = []
    for i in range(startNum, endNum):
        ans.append(squaresum(i))
    return ans


def squaresum(n: int)-> int:
    # Iterate i from 1
    # and n finding
    # square of i and
    # add to sum.
    sm = 0
    for i in range(1, n+1):
        sm = sm + (i * i)

    return sm