import unittest
from datetime import datetime, date, time, timedelta
from market_analytics import get_market_seconds_between_events

class TestMarketAnalytics(unittest.TestCase):
    def setUp(self):
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)
        
        # Generate trading days for July 2024 (weekdays only)
        # Covering enough range for all examples
        self.trading_days = []
        d = date(2024, 7, 1)
        end_date = date(2024, 7, 15)
        while d <= end_date:
            if d.weekday() < 5: # 0-4 are Mon-Fri
                self.trading_days.append(d)
            d += timedelta(days=1)
        self.trading_days.sort()

    def test_example_cases(self):
        events = [
            # 1. Mon Jul 1 09:00 -> Mon Jul 1 09:00
            (datetime(2024, 7, 1, 9, 0, 0), datetime(2024, 7, 1, 9, 0, 0)),
            
            # 2. Mon Jul 1 09:00 -> Mon Jul 1 09:30
            (datetime(2024, 7, 1, 9, 0, 0), datetime(2024, 7, 1, 9, 30, 0)),
            
            # 3. Mon Jul 1 09:00 -> Mon Jul 1 09:30:01
            (datetime(2024, 7, 1, 9, 0, 0), datetime(2024, 7, 1, 9, 30, 1)),
            
            # 4. Mon Jul 1 09:00 -> Mon Jul 1 16:00
            (datetime(2024, 7, 1, 9, 0, 0), datetime(2024, 7, 1, 16, 0, 0)),
            
            # 5. Mon Jul 1 09:00 -> Mon Jul 1 17:00
            (datetime(2024, 7, 1, 9, 0, 0), datetime(2024, 7, 1, 17, 0, 0)),
            
            # 6. Fri Jul 5 09:00 -> Fri Jul 5 17:00
            (datetime(2024, 7, 5, 9, 0, 0), datetime(2024, 7, 5, 17, 0, 0)),
            
            # 7. Fri Jul 5 09:00 -> Mon Jul 8 09:30
            (datetime(2024, 7, 5, 9, 0, 0), datetime(2024, 7, 8, 9, 30, 0)),
            
            # 8. Fri Jul 5 09:00 -> Mon Jul 8 09:30:01
            (datetime(2024, 7, 5, 9, 0, 0), datetime(2024, 7, 8, 9, 30, 1)),
            
            # 9. Thu Jul 4 16:00 -> Fri Jul 5 09:30
            (datetime(2024, 7, 4, 16, 0, 0), datetime(2024, 7, 5, 9, 30, 0)),
            
            # 10. Thu Jul 4 16:00 -> Fri Jul 5 09:30:01
            (datetime(2024, 7, 4, 16, 0, 0), datetime(2024, 7, 5, 9, 30, 1)),
        ]
        
        expected_results = [
            0,      # 1
            0,      # 2
            1,      # 3
            23400,  # 4
            23400,  # 5
            23400,  # 6
            23400,  # 7
            23401,  # 8
            0,      # 9
            1       # 10
        ]
        
        results = get_market_seconds_between_events(events, self.trading_days, self.market_open, self.market_close)
        
        self.assertEqual(results, expected_results)

    def test_single_event(self):
        # Test passing a single event to ensure list handling is correct
        events = [(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0))]
        results = get_market_seconds_between_events(events, self.trading_days, self.market_open, self.market_close)
        self.assertEqual(results, [3600])

    def test_no_trading_days(self):
        # Empty trading days list
        events = [(datetime(2024, 7, 1, 10, 0), datetime(2024, 7, 1, 11, 0))]
        results = get_market_seconds_between_events(events, [], self.market_open, self.market_close)
        self.assertEqual(results, [0])

    def test_event_outside_range(self):
        # Event completely outside generated trading days (e.g. year 2025)
        events = [(datetime(2025, 7, 1, 10, 0), datetime(2025, 7, 1, 11, 0))]
        results = get_market_seconds_between_events(events, self.trading_days, self.market_open, self.market_close)
        self.assertEqual(results, [0])

if __name__ == '__main__':
    unittest.main()
