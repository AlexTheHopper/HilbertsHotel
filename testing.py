"""
Module docstring
"""
import random
import numpy as np
def test_func(a, b):
    """
    Bing bong
    """
    if a % 2 == 0:
        return a
    return b

def test(a):
    if a > 2:
        a = 0
        return True
    else:
        return False
    
testdict = {0: 'zero',
            1: 'one',
            2: 'three',
            4: 'four'}
print(list(testdict.keys()))

for i in np.linspace(-5, 5, 11):
    print(f'number is {i} and bool is {'True' if i else 'False'}')