from typing import Any, List, Dict
import json

# --- Mock LLM Client (for offline testing) ---
class MockLLM:
    def chat(self, messages, tools):
        """
        Simulate an LLM response based on the query.
        """
        last_msg = messages[-1]['content']
        if "Apple" in last_msg and "Microsoft" in last_msg:
            # Simulate a multi-tool call request
            return {
                "tool_calls": [
                    {"name": "get_stock_price", "args": {"symbol": "AAPL"}},
                    {"name": "get_stock_price", "args": {"symbol": "MSFT"}}
                ],
                "content": None # LLM decides to call tools first
            }
        elif "tool_result" in messages[-1]:
            # Simulate final answer after tool execution
            return {
                "tool_calls": [],
                "content": " Based on the prices, the total is $330."
            }
        return {"content": "I don't know."}

# --- Tools Implementation ---
def get_stock_price(symbol: str) -> float:
    print(f"Executing: get_stock_price('{symbol}')")
    # Mock data
    prices = {"AAPL": 150.0, "MSFT": 180.0, "GOOGL": 2800.0}
    return prices.get(symbol.upper(), 0.0)

def calculate(expression: str) -> float:
    print(f"Executing: calculate('{expression}')")
    try:
        return eval(expression, {"__builtins__": None}, {})
    except:
        return 0.0

# Tool Registry
available_tools = {
    "get_stock_price": get_stock_price,
    "calculate": calculate
}

tool_definitions = [
    {
        "name": "get_stock_price",
        "description": "Get the current stock price for a given symbol.",
        "parameters": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"]
        }
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"]
        }
    }
]

# --- Agent Logic ---
class SimpleAgent:
    def __init__(self, client):
        self.client = client
        self.messages = []

    def run(self, user_query: str):
        self.messages.append({"role": "user", "content": user_query})
        
        # Turn 1: LLM decides actions
        response = self.client.chat(self.messages, tool_definitions)
        
        # Handle Tool Calls
        if response.get("tool_calls"):
            tool_outputs = []
            
            # Optimization: Execute all tool calls in parallel (simulated here)
            # This reduces latency compared to sequential wait-and-call
            for tool_call in response["tool_calls"]:
                name = tool_call["name"]
                args = tool_call["args"]
                
                if name in available_tools:
                    result = available_tools[name](**args)
                    tool_outputs.append({
                        "role": "tool_result",
                        "name": name,
                        "content": str(result)
                    })
            
            # Append results to history
            self.messages.extend(tool_outputs)
            
            # Turn 2: LLM generates final answer
            # In a real agent loop, this would be `while response.tool_calls:`
            final_response = self.client.chat(self.messages, tool_definitions)
            return final_response["content"]
            
        return response["content"]

if __name__ == "__main__":
    agent = SimpleAgent(MockLLM())
    query = "What is the price of Apple plus Microsoft?"
    print(f"User: {query}")
    print("--- Execution ---")
    answer = agent.run(query)
    print("--- Result ---")
    print(f"Agent: {answer}")
