import numpy as np

#print list(itertools.permutations([1, 2, 3]))

matrix = [[1, 2, 3],
          [2, 3, 4],
          [3, 4, 5]]

permutation = [1, 0, 2]

def permute_array(MM, perm):
    tempMM0 = np.asarray(MM)
    tempMM1 = np.asarray([tempMM0[i, :] for i in perm])
    tempMM2 = np.asarray([tempMM1[:, i] for i in perm])
    return tempMM2

print permute_array(matrix, permutation)