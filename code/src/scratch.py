import numpy as np

#nodeindices = [0, 1, 2]

#print list(itertools.permutations([1, 2, 3]))

matrix = [[1, 2, 3],
          [2, 3, 4],
          [3, 4, 5]]

permutation = [1, 0, 2]

MM = np.asarray(matrix)

result1 = np.asarray([MM[i, :] for i in permutation])
print result1

result2 = np.asarray([result1[:, i] for i in permutation])
print result2