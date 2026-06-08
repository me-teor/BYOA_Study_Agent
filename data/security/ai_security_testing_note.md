# AI Testing and Security

When LLMs write code, testing and security become more important because generated code may contain hidden defects or vulnerabilities.

## Traditional Security Techniques

### SAST

Static Application Security Testing analyzes source code or binaries without running the program. It can detect issues such as SQL injection, command injection, and cross-site scripting.

### DAST

Dynamic Application Security Testing tests a running application from the outside. It simulates real attacks and can reveal runtime vulnerabilities.

### SCA

Software Composition Analysis checks open-source dependencies and transitive dependencies for known vulnerabilities.

## AI Agent Attack Vectors

New AI-related risks include:

1. Prompt injection: hidden instructions that make the model deviate from its intended behavior.
2. Tool misuse: manipulating the agent to abuse tools.
3. Intent breaking: redirecting the agent away from the user's original task.
4. Identity spoofing: pretending to be a trusted user or agent.
5. Code attacks: using generated or executed code to compromise the environment.

## Best Practices

AI-generated code should be reviewed, tested, scanned, and monitored. Security-sensitive changes need extra caution.
