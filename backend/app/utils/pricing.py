"""Pricing utilities for Gemini models."""

# Pricing per 1M tokens (USD)
# Source: Google Cloud Vertex AI Pricing (Approximate for Hackathon)
PRICING_GEMINI_FLASH = {
    "input": 0.10,   # $0.10 / 1M tokens
    "output": 0.40   # $0.40 / 1M tokens
}

PRICING_GEMINI_PRO = {
    "input": 0.50,
    "output": 1.50
}

def calculate_gemini_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for Gemini API usage.
    
    Args:
        model_name: Name of the model (e.g. 'gemini-1.5-flash', 'gemini-pro')
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Cost in USD
    """
    if "flash" in model_name.lower():
        input_price = PRICING_GEMINI_FLASH["input"]
        output_price = PRICING_GEMINI_FLASH["output"]
    else:
        # Fallback to Pro pricing
        input_price = PRICING_GEMINI_PRO["input"]
        output_price = PRICING_GEMINI_PRO["output"]
        
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    
    return round(input_cost + output_cost, 6)
