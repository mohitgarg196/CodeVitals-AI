# CodeVitals-AI

> Agentic AI software engineer for security analysis,
> performance optimization, automated fixing, and
> sandbox-based verification.

## 🚧 Project Status

Currently building **V0 — Full-Context LLM Baseline**.

## 🧭 Evolution

```text
V0
Full-Context LLM
     │
     ▼
V1
Tool-Using Agent
     │
     ▼
V2
Agent Harness
     │
     ▼
V3
Security + Optimization Engine
     │
     ▼
V4
Context Engineering
     │
     ▼
V5
MCP + RAG
     │
     ▼
V6
Sandbox + Verification
     │
     ▼
V7
Evaluation + Model Routing


======================================================================================================


V0 — Full-Context LLM Baseline
Architecture

Repository
     │
     ▼
Read all source files
     │
     ▼
Full Repository Context
     │
     ▼
Gemini
     │
     ▼
Structured Analysis Report


V0 Metrics:
========== SECUREOPT REPORT ==========

Finding #1
Category      : Database Inefficiency
Severity      : Medium
File          : inefficient.py
Line          : 5
Title         : N+1 Database Query Pattern
Description   : Executing a database query inside a loop causes N+1 query performance degradation as the size of user_ids increases.
Recommendation: Batch the database query into a single call, for example using db.find({'id': {'$in': user_ids}}).
------------------------------------------------------------
Finding #2
Category      : Security Vulnerability
Severity      : High
File          : vulnerable.py
Line          : 8
Title         : SQL Injection
Description   : Dynamically constructing SQL queries using f-string interpolation allows untrusted input to alter query logic.
Recommendation: Use parameterized queries, for example conn.execute('SELECT * FROM users WHEREid = ?', (user_id,)).
------------------------------------------------------------
Finding #3
Category      : Security Vulnerability
Severity      : High
File          : vulnerable.py
Line          : 15
Title         : Command Injection
Description   : Passing unvalidated input directly to os.system allows execution of arbitrary shell commands.
Recommendation: Avoid os.system. Use the subprocess module with argument sequences and shell=False, or restrict commands to an explicit allowlist.
------------------------------------------------------------
Finding #4
Category      : Security Vulnerability
Severity      : High
File          : vulnerable.py
Line          : 19
Title         : Arbitrary Code Execution
Description   : Passing user-controlled strings to eval allows execution of arbitrary Python code in the current execution context.
Recommendation: Avoid eval. Use safe parsers such as ast.literal_eval for basic data types or construct a restricted domain-specific parser.
------------------------------------------------------------

========== METRICS ==========
Latency        : 31.56s
Findings       : 4
Input tokens   : 287
Output tokens  : 463
Total tokens   : 3315


===============================================================================================================

V1

                    ┌──────────────┐
                    │    Gemini    │
                    │    Agent     │
                    └──────┬───────┘
                           │
                    "I need information"
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
        list_files    search_code    read_file
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                      Observation
                           ↓
                         Gemini
                           │
                    ┌──────┴──────┐
                    ↓             ↓
                  More?          Done
                    │             │
                    └─── loop     ↓
                                Report


Reading repository...
Repository loaded.
Repository characters: 529

Sending repository to Gemini...
Warning: there are non-text parts in the response: ['thought_signature'], returning concatenated parsed result from text parts. Check the full candidates.content.parts accessor to get the full model response.

========== SECUREOPT REPORT ==========

Finding #1
Category      : Performance
Severity      : Medium
File          : inefficient.py
Line          : 4
Title         : N+1 Query Inefficiency in Database Lookup
Description   : The get_users function executes a database query inside a loop for each user ID, leading to an N+1 query pattern and significant database latency.
Recommendation: Use a bulk query operator such as $in to fetch all users in a single database round-trip.
------------------------------------------------------------
Finding #2
Category      : Security
Severity      : High
File          : vulnerable.py
Line          : 8
Title         : SQL Injection in get_user
Description   : User input is interpolated directly into a SQL query string using f-strings, allowing SQL injection.
Recommendation: Use parameterized queries with placeholder bindings instead of string formatting.
------------------------------------------------------------
Finding #3
Category      : Security
Severity      : High
File          : vulnerable.py
Line          : 14
Title         : Command Injection in run_command
Description   : Passing input directly to os.system enables shell command injection.
Recommendation: Avoid os.system and use the subprocess module with shell=False and input passed as an argument vector.
------------------------------------------------------------
Finding #4
Category      : Security
Severity      : High
File          : vulnerable.py
Line          : 18
Title         : Arbitrary Code Execution in evaluate
Description   : The eval function executes arbitrary Python code from string inputs.
Recommendation: Avoid using eval on dynamic or untrusted inputs; use safe evaluation methods such as ast.literal_eval where appropriate.
------------------------------------------------------------

========== METRICS ==========
Latency        : 21.95s
Findings       : 4
Input tokens   : 287
Output tokens  : 297
Total tokens   : 2836
