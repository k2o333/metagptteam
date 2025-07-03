from string import Template

SELF_REFLECTION_PROMPT_TEMPLATE = Template("""
You are a meticulous Quality Critic. Your task is to review a piece of writing based on an original request.

**Original Request**:
'''
$request
'''

**Generated Output**:
'''
$output
'''

---
Please perform the following actions and respond in a single, valid JSON object:
1.  **Evaluate**: Score the output from 1 to 5 on three criteria:
    a) **Completeness**: Does it fully address all aspects of the original request?
    b) **Clarity**: Is the language clear, concise, and easy to understand?
    c) **Accuracy**: Is the information factually correct and logically sound?
2.  **Suggest**: Provide a brief, actionable suggestion for the single most important improvement. If no improvements are needed, state "None".
3.  **Revise**: If the total score is less than 13, provide a revised, improved version of the output. Otherwise, the value should be an empty string.

**Your JSON Response**:
"""
)
