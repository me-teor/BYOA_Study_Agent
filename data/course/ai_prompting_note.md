# Prompting Techniques

## Zero-shot Prompting

Zero-shot prompting means asking an LLM to complete a task without providing examples. It is simple and direct, but may be less reliable for tasks requiring a specific format or domain-specific style.

## K-shot Prompting

K-shot prompting provides several examples before asking the model to complete a similar task. It is useful for enforcing style, naming conventions, output format, or domain-specific behavior.

## Chain-of-Thought Prompting

Chain-of-thought prompting asks the model to reason through a task step by step. It is useful for programming, mathematics, debugging, and other multi-step reasoning tasks.

## Self-consistency Prompting

Self-consistency prompting samples multiple reasoning paths and selects the most common or most reliable answer. It can reduce hallucinations and improve answer reliability.

## Reflexion

Reflexion asks the model to critique its previous output, identify possible problems, and revise the answer. It is commonly used in autonomous coding agents and iterative debugging workflows.
