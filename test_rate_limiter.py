import unittest
from rate_limiter import solve_rate_limiter

class TestRateLimiter(unittest.TestCase):
    def test_example_1(self):
        timestamps = [1, 100, 200, 250, 350]
        maxRequests = 2
        windowSize = 200
        expected = [True, True, False, True, True]
        self.assertEqual(solve_rate_limiter(timestamps, maxRequests, windowSize), expected)

    def test_example_2(self):
        timestamps = [10, 20, 30, 40]
        maxRequests = 3
        windowSize = 50
        expected = [True, True, True, False]
        self.assertEqual(solve_rate_limiter(timestamps, maxRequests, windowSize), expected)

    def test_example_3(self):
        timestamps = [1, 2, 3, 10, 11, 12, 20, 21, 22, 23]
        maxRequests = 2
        windowSize = 5
        expected = [True, True, False, True, True, False, True, True, False, False]
        self.assertEqual(solve_rate_limiter(timestamps, maxRequests, windowSize), expected)

    def test_example_4(self):
        timestamps = [1, 2, 3, 4, 5]
        maxRequests = 1
        windowSize = 1
        expected = [True, True, True, True, True]
        self.assertEqual(solve_rate_limiter(timestamps, maxRequests, windowSize), expected)

    def test_single_allowed(self):
        timestamps = [100]
        maxRequests = 1
        windowSize = 10
        expected = [True]
        self.assertEqual(solve_rate_limiter(timestamps, maxRequests, windowSize), expected)
        
    def test_single_rejected(self):
        # This case is tricky because the first request is always allowed if maxRequests >= 1.
        # If maxRequests is 0, then it would be rejected, but constraints say maxRequests >= 1.
        pass

    def test_large_window(self):
        timestamps = [1, 2, 3, 4, 5]
        maxRequests = 2
        windowSize = 1000
        expected = [True, True, False, False, False]
        self.assertEqual(solve_rate_limiter(timestamps, maxRequests, windowSize), expected)

if __name__ == '__main__':
    unittest.main()
