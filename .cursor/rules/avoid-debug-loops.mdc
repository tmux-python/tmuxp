---
description: When stuck in debugging loops, break the cycle by minimizing to an MVP, removing debugging cruft, and documenting the issue completely for a fresh approach
globs: *.py
alwaysApply: true
---
# Avoid Debug Loops

When debugging becomes circular and unproductive, follow these steps:

## Detection
- You have made multiple unsuccessful attempts to fix the same issue
- You are adding increasingly complex code to address errors
- Each fix creates new errors in a cascading pattern
- You are uncertain about the root cause after 2-3 iterations

## Action Plan

1. **Pause and acknowledge the loop**
   - Explicitly state that you are in a potential debug loop
   - Review what approaches have been tried and failed

2. **Minimize to MVP**
   - Remove all debugging cruft and experimental code
   - Revert to the simplest version that demonstrates the issue
   - Focus on isolating the core problem without added complexity

3. **Comprehensive Documentation**
   - Provide a clear summary of the issue
   - Include minimal but complete code examples that reproduce the problem
   - Document exact error messages and unexpected behaviors
   - Explain your current understanding of potential causes

4. **Format for Portability**
   - Present the problem in quadruple backticks for easy copying:

````
# Problem Summary
[Concise explanation of the issue]

## Minimal Reproduction Code
```python
# Minimal code example that reproduces the issue
```

## Error/Unexpected Output
```
[Exact error messages or unexpected output]
```

## Failed Approaches
[Brief summary of approaches already tried]

## Suspected Cause
[Your current hypothesis about what might be causing the issue]
````

This format enables the user to easily copy the entire problem statement into a fresh conversation for a clean-slate approach.
