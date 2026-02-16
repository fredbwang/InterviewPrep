from datetime import datetime, date, time
import bisect

def get_market_seconds_between_events(events, trading_days, market_open, market_close):
    """
    Calculates the seconds between events considering only market hours.

    Args:
        events: A list of n tuples. Each tuple has (start, end) datetimes.
        trading_days: A sorted list of datetime.dates.
        market_open: A datetime.time specifying when the market opens.
        market_close: A datetime.time specifying when the market closes.

    Returns:
        int [n]: the number of seconds between each pair of (start, end).
    """
    results = []

    for start, end in events:
        total_seconds = 0.0
        
        start_date = start.date()
        end_date = end.date()
        
        # Find the range of trading days that could possibly intersect with the event
        idx_start = bisect.bisect_left(trading_days, start_date)
        idx_end = bisect.bisect_right(trading_days, end_date)
        
        relevant_days = trading_days[idx_start:idx_end]
        
        for current_day in relevant_days:
            # Construct market open and close datetimes for the current day
            current_market_open = datetime.combine(current_day, market_open)
            current_market_close = datetime.combine(current_day, market_close)
            
            # Handle timezone awareness if input events are aware
            if start.tzinfo is not None and current_market_open.tzinfo is None:
                current_market_open = current_market_open.replace(tzinfo=start.tzinfo)
                current_market_close = current_market_close.replace(tzinfo=start.tzinfo)
            
            # Determine the overlap between the event interval and the market hours
            # Interval 1: [start, end]
            # Interval 2: [current_market_open, current_market_close]
            
            overlap_start = max(start, current_market_open)
            overlap_end = min(end, current_market_close)
            
            if overlap_start < overlap_end:
                total_seconds += (overlap_end - overlap_start).total_seconds()
        
        results.append(int(total_seconds))
        
    return results
