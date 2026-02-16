# import requests # Uncomment this line when requests is installed
import sys

def getTransactions(txnType, locationId):
    """
    Retrieves transactions from the REST API, filters by location, and aggregates by user.
    
    Note: As per requirements, this script ONLY prints the URL that would be called
    and does not execute the actual HTTP request.
    
    Required Libraries:
    - requests (pip install requests)
    """
    
    # Initialize variables
    page = 1
    total_pages = 1 # Placeholder, would be updated from first API response
    user_totals = {}
    
    print("Required Python libraries: requests (pip install requests)")
    print(f"Processing transactions for txnType='{txnType}', locationId={locationId}")

    while page <= total_pages:
        # Construct the URL
        url = f"https://jsonmock.hackerrank.com/api/transactions/search?txnType={txnType}&page={page}"
        
        # REQUIREMENT: Only print out the url
        print(f"API Call: {url}")
        
        # --------------------------------------------------------------------------
        # LOGIC BELOW IS COMMENTED OUT TO SATISFY "NO ACTUAL CALL" REQUIREMENT
        # --------------------------------------------------------------------------
        
        # --- Option 1: Using requests (External Library) ---
        # import requests
        # response = requests.get(url)
        # if response.status_code != 200:
        #     print(f"Error: API returned status code {response.status_code}")
        #     break
        # data = response.json()
        
        # --- Option 2: Using urllib (Standard Library - No Install Needed) ---
        # import urllib.request
        # import json
        # with urllib.request.urlopen(url) as response:
        #     if response.getcode() != 200:
        #         print(f"Error: API returned status code {response.getcode()}")
        #         break
        #     data = json.loads(response.read().decode())

        # total_pages = data['total_pages']
        
        # for record in data['data']:
        #     # Filter by location ID
        #     if record['location']['id'] == locationId:
        #         # Parse amount: remove '$' and ',' then convert to float
        #         amount_str = record['amount'].replace('$', '').replace(',', '')
        #         amount = float(amount_str)
        #         
        #         userId = record['userId']
        #         if userId in user_totals:
        #             user_totals[userId] += amount
        #         else:
        #             user_totals[userId] = amount
        # --------------------------------------------------------------------------
        
        # Increment page for the loop (in a real scenario)
        page += 1
        
        # Break immediately since we can't allow the loop to run with mocked total_pages=1 forever if logic was different,
        # or implies single page check. Here total_pages=1 so it runs once and finishes.
        break

    # --------------------------------------------------------------------------
    # RESULT RETURN LOGIC (COMMENTED OUT)
    # --------------------------------------------------------------------------
    # result = [[uid, total] for uid, total in user_totals.items()]
    # result.sort(key=lambda x: x[0]) # Sort by userId ascending
    # return result
    return []

if __name__ == "__main__":
    # Example usage
    getTransactions("debit", 1)
