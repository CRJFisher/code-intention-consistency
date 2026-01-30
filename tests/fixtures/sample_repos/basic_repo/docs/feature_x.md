# Feature X Documentation

## Overview

Feature X provides basic arithmetic operations.

## Calculator Module

### add(a, b)

Adds two numbers together.

**Parameters:**
- `a` (int): First number
- `b` (int): Second number

**Returns:**
- int: Sum of a and b

**Example:**
```python
from src.feature_x.calculator import add
result = add(2, 3)  # Returns 5
```

## Behavior Y {#behavior-y}

The add function implements simple integer addition with the following guarantees:
- Works with positive and negative integers
- Handles zero correctly
- Returns an integer result
