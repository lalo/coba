import math
import random
import timeit

from collections import defaultdict
from itertools import count
from typing import Iterator, Sequence

import unittest

import coba.random

class Random_Tests(unittest.TestCase):

    @staticmethod
    def _failure_rate(trials:int, generator: Iterator[Sequence[int]], alpha: float = .001):
        """
            p-value seemed a little unreliable on _cumsum_test so instead we use a
            repeated test to calculate a more stable failure rate based on p-value.
        """

        failed_to_reject_rate = 0

        for _ in range(trials):
            random_walk = next(generator)

            p = Random_Tests._cumsum_test(random_walk)
            failed_to_reject_rate += (p > alpha)/trials

        return failed_to_reject_rate

    @staticmethod
    def _cumsum_test(random_walk:Sequence[int]):
        """A statistical test to determine if the random_walk is uniformly random.

        Args:
            random_walk: A sequence of -1 and 1 representing steps in the set of integers.

        Remarks:
            This test is taken from https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/cusumtes.htm.
            My implementation doesn't seem to be work particularly though. I seem to incorrectly reject the null at
            higher rate than my alpha of .001 should allow.
        """

        def phi(x):
            return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
        
        cumsum = random_walk[0]
        z      = random_walk[0]

        for x in random_walk[1::]:
            cumsum += x
            z = max(z, abs(cumsum))

        n         = len(random_walk)
        k_bound_1 = ( int((-n/z+1)/4), int((n/z-1)/4) )
        k_bound_2 = ( int((-n/z-3)/4), int((n/z-1)/4) )

        sum1 = sum([ phi( (4*k+1)*z ) - phi( (4*k-1)*z ) for k in range(k_bound_1[0], k_bound_1[1])])
        sum2 = sum([ phi( (4*k+3)*z ) - phi( (4*k+1)*z ) for k in range(k_bound_2[0], k_bound_2[1])])

        p = 1- sum1 + sum2

        return p

    def test_speed_of_randoms(self):
        
        time = min(timeit.repeat(lambda:coba.random.randoms(5000), repeat=200, number=1))

        #was approximately 0.0025
        self.assertLess(time,.005)

    def test_value_of_randoms(self):

        numbers = coba.random.randoms(500000)

        self.assertEqual(len(numbers), 500000)

        for n in numbers:
            self.assertLessEqual(n, 1)
            self.assertGreaterEqual(n, 0)

    def test_speed_of_shuffle(self):

        to_shuffle = list(range(50000))

        time = min(timeit.repeat(lambda:coba.random.shuffle(to_shuffle), repeat=20, number=1))
        
        #was approximately 0.057
        self.assertLess(time,1)

    def test_value_of_shuffle(self):

        numbers = coba.random.shuffle(list(range(500000)))

        self.assertEqual(len(numbers), 500000)
        self.assertNotEqual(numbers, list(range(500000)))

    def test_randoms_repetability(self):

        coba.random.seed(10)

        actual_random_numbers_1 = coba.random.randoms(5)

        coba.random.seed(10)

        actual_random_numbers_2 = coba.random.randoms(5)

        self.assertSequenceEqual(actual_random_numbers_1, actual_random_numbers_2)

    def test_randoms_is_uniform_0_1(self):
        #this test will fail maybe 1% of the time
        
        walks = 2000
        steps = 100

        coba_random_walk = ([-1 if n < 0.5 else 1 for n in coba.random.randoms(steps)] for _ in count()) 
        std_random_walk  = ([-1 if random.random() < 0.5 else 1 for _ in range(steps)] for _ in count())

        coba_failure_rate = self._failure_rate(walks, coba_random_walk)
        std_failure_rate = self._failure_rate(walks, std_random_walk)

        if((coba_failure_rate-std_failure_rate)/std_failure_rate > .25):
            print(f"\n{coba_failure_rate}")
            print(f"\n{std_failure_rate}")

        self.assertLess((coba_failure_rate-std_failure_rate)/std_failure_rate, .25)

    def test_shuffle_is_truly_random_and_independent_of_order(self):
        # this test uses a hypthoesis test taken from the link below. This test is expected
        # have a certain number of "false positives". So if this test simply failed once and passes
        # every time after you can simply ignore the failure as one of those "false positives".
        # https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/cusumtes.htm
        
        walks = 1000
        steps = 50

        base_walks = [sorted([-1 if random.random() < 0.5 else 1 for _ in range(steps)]) for _ in range(walks)]

        def coba_shuffle() -> Iterator[Sequence[int]]:
            for base_walk in base_walks:                
                yield coba.random.shuffle(base_walk)

        def std_shuffle() -> Iterator[Sequence[int]]:
            for base_walk in base_walks:
                
                base_walk_copy = base_walk.copy()
                random.shuffle(base_walk_copy)
                
                yield base_walk_copy

        coba_failure_rate = self._failure_rate(walks, coba_shuffle())
        std_failure_rate = self._failure_rate(walks, std_shuffle())

        if (coba_failure_rate-std_failure_rate)/std_failure_rate > .1:
            print(f"\n{coba_failure_rate}")
            print(f"\n{std_failure_rate}")

        self.assertLess((coba_failure_rate-std_failure_rate)/std_failure_rate , .1)

    def test_randint_is_bound_correctly_1(self):
        observed_ints = set()

        for i in range(100):
            observed_ints.add(coba.random.randint(0,2))

        self.assertIn(0, observed_ints)
        self.assertIn(1, observed_ints)
        self.assertIn(2, observed_ints)

    def test_randint_is_bound_correctly_2(self):
        observed_ints = set()

        for i in range(100):
            observed_ints.add(coba.random.randint(-3,-1))

        self.assertIn(-3, observed_ints)
        self.assertIn(-2, observed_ints)
        self.assertIn(-1, observed_ints)

    def test_randint_is_uniform(self):

        obs_count = defaultdict(int)

        n_samples = 5000
        expected  = n_samples/6

        for i in range(n_samples):
            obs_count[coba.random.randint(1,6)] += 1

        chi_squared = sum([ (observed - expected)**2/expected for observed in obs_count.values() ])
        
        #assuming degrees of freedom equals 5 (this will change if lower or upper are changed above)
        #then chi_squared >= 15 would cause us to reject the null incorrectly less than 1% of the time

        self.assertLess(chi_squared, 15)        

    def test_choice1(self):
        choices = [(0,1), (1,0)]

        choice = coba.random.choice(choices)

        self.assertIsInstance(choice, tuple)

    def test_choice2(self):
        weights = [0.5,0.5]
        choices = [(0,1), (1,0)]

        choice = coba.random.choice(choices,weights)

        self.assertIsInstance(choice, tuple)

if __name__ == '__main__':
    unittest.main()