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
========== CODEVITALS REPORT ==========

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

V1 METRICS:

========== CODEVITALS REPORT ==========

Finding #1
Category      : Security
Severity      : High
File          : vulnerable.py
Line          : 8
Title         : SQL Injection Vulnerability
Description   : The get_user function constructs a SQL query using string formatting with user_id, making it vulnerable to SQL injection attacks.
Recommendation: Use parameterized queries with placeholders (e.g., cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))) to safely query the database.
------------------------------------------------------------
Finding #2
Category      : Security
Severity      : High
File          : vulnerable.py
Line          : 14
Title         : Command Injection Vulnerability
Description   : The run_command function uses os.system to execute shell commands directly from untrusted input, allowing arbitrary command execution.
Recommendation: Avoid executing system commands directly. If necessary, use subprocess.run with arguments passed as a list and shell=False.
------------------------------------------------------------
Finding #3
Category      : Security
Severity      : High
File          : vulnerable.py
Line          : 18
Title         : Arbitrary Code Execution
Description   : The evaluate function uses eval() to parse expressions, which allows arbitraryPython code execution if untrusted input is passed.
Recommendation: Avoid using eval(). Use safer alternatives such as ast.literal_eval() for literal structures or a dedicated expression parser.
------------------------------------------------------------
Finding #4
Category      : Performance
Severity      : Medium
File          : inefficient.py
Line          : 4
Title         : N+1 Database Query Bottleneck
Description   : The get_users function executes a database query inside a loop for each user_id, causing an N+1 query performance bottleneck.
Recommendation: Batch the query using a single database call with an $in operator, e.g., db.find({'id': {'$in': user_ids}}).
------------------------------------------------------------

========== V1 METRICS ==========
Latency               : 55.07s
Total findings        : 4
Security findings     : 3
Optimization findings : 1
Tool calls            : 3
Input tokens          : 838
Output tokens         : 355
Total tokens          : 3474


=======================================================================================================

V2 Architecture: 

                         CodeVitals
                              │
                              ▼
                       ┌─────────────┐
                       │    Agent    │
                       │   Gemini    │
                       └──────┬──────┘
                              │
                       "I want to..."
                              │
                              ▼
                    ┌──────────────────┐
                    │  AGENT HARNESS   │
                    │                  │
                    │  Policy          │
                    │  Permissions     │
                    │  Budget          │
                    │  State           │
                    │  Loop Detection  │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                  ALLOW             BLOCK
                    │
                    ▼
                  Tools


LLM
 │
 │ "I want to execute X"
 ▼
HARNESS
 │
 ├── Is X allowed?
 ├── Is budget available?
 ├── Is this a repeated action?
 ├── Is the path safe?
 │
 ▼
Tool execution
