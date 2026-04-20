# BugHound Mini Model Card (Reflection)

Fill this out after you run BugHound in **both** modes (Heuristic and Gemini).

---

## 1) What is this system?

**Name:** BugHound  
**Purpose:** Analyze a Python snippet, propose a fix, and run reliability checks before suggesting whether the fix should be auto-applied.

**Intended users:** Students learning agentic workflows and AI reliability concepts.

---

## 2) How does it work?

Describe the workflow in your own words (plan → analyze → act → test → reflect).  
Include what is done by heuristics vs what is done by Gemini (if enabled).

It plans a quick scan of the snippet, analyzes problems with heuristics in offline mode or Gemini when an API key is available, proposes a fix either via heuristics or the LLM, assesses the risk of the proposed fix, and then reflects on whether the fix is safe enough to auto-apply. In offline mode the system uses simple pattern-based checks like "print(" and bare "except:" detection. In Gemini mode, it would rely on the model for richer issue detection and code rewriting, while still enforcing local guardrails.

---

## 3) Inputs and outputs

**Inputs:**

- What kind of code snippets did you try?
- What was the “shape” of the input (short scripts, functions, try/except blocks, etc.)?

- Short Python snippets such as small functions, "try/except" blocks, print statements, and comment-only code.
- Sample inputs included "cleanish.py" (clean function with logging), "mixed_issues.py" (TODO, print, bare except), and a comment-only case.

**Outputs:**

- What types of issues were detected?
- What kinds of fixes were proposed?
- What did the risk report show?

- Detected issues are returned as a list of typed objects with "type", "severity", and "msg" fields.
- Fixes are proposed either by simple heuristics (e.g. replacing "print" with "logging.info" and changing "except:" to "except Exception as e:") or by the LLM output when enabled.
- The risk report shows a score, level, reasons, and "should_autofix" decision.

---

## 4) Reliability and safety rules

List at least **two** reliability rules currently used in `assess_risk`. For each:

- What does the rule check?
- Why might that check matter for safety or correctness?
- What is a false positive this rule could cause?
- What is a false negative this rule could miss?

1. **No fix is high risk**  
   - Checks whether the fixed code is empty.  
   - This matters because an empty fix means the agent failed to produce a usable result.  
   - False positive: a harmless no-op fix could be classified as high risk even if no change was needed.  
   - False negative: if the fix is non-empty but invalid, this rule does not catch it.

2. **Return removal penalty**  
   - Checks whether the original code contained "return" but the fixed code does not.  
   - This matters because removing return behavior can silently break program semantics.  
   - False positive: a valid refactor that intentionally removes an unused return value could be penalized.  
   - False negative: it misses other behavior changes that do not involve "return".

3. **Code expansion risk**  
   - Checks whether fixed code is more than 1.5× longer than the original.  
   - This matters because overly large fixes are more likely to introduce unintended changes.  
   - False positive: a legitimate fix that adds required boilerplate could be flagged as risky.  
   - False negative: it does not catch large semantic changes that keep roughly the same line count.

---

## 5) Observed failure modes

Provide at least **two** examples:

1. A time BugHound missed an issue it should have caught  
2. A time BugHound suggested a fix that felt risky, wrong, or unnecessary  

For each, include the snippet (or describe it) and what went wrong.

1. **Missed issue example**: A comment-only snippet contains no executable code. The analyzer reports no issues, which is reasonable, but the agent could still accept a low-risk status without any useful action. This shows the system can treat harmless inputs as fully safe.

2. **Risky fix example**: The offline "MockClient" fixer returned a comment-only placeholder message instead of a real code rewrite. Without the new guardrail, that output would have been accepted as a fix, which felt wrong and unsafe.

---

## 6) Heuristic vs Gemini comparison

Compare behavior across the two modes:

- What did Gemini detect that heuristics did not?
- What did heuristics catch consistently?
- How did the proposed fixes differ?
- Did the risk scorer agree with your intuition?

- Heuristics consistently catch obvious patterns like "print" statements, bare "except:", and TODO comments.  
- Gemini is expected to detect more nuanced issues and generate more natural code rewrites, but it still needs validation and fallback logic.  
- Proposed fixes from heuristics are predictable and minimal, while Gemini fixes can be more creative and potentially more risky.  
- The risk scorer generally agrees with intuition when it flags large or structurally different rewrites as higher risk.

---

## 7) Human-in-the-loop decision

Describe one scenario where BugHound should **refuse** to auto-fix and require human review.

- What trigger would you add?
- Where would you implement it (risk_assessor vs agent workflow vs UI)?
- What message should the tool show the user?

One scenario where BugHound should refuse to auto-fix is when the proposed fix is syntactically valid but contains no executable code or is much larger than the original. This trigger belongs in the agent workflow because it is a guardrail on the LLM output before risk assessment. The tool should show a message like: “LLM output did not contain a usable code fix; using heuristic fallback for safety.”

---

## 8) Improvement idea

Propose one improvement that would make BugHound more reliable *without* making it dramatically more complex.

Examples:

- A better output format and parsing strategy
- A new guardrail rule + test
- A more careful “minimal diff” policy
- Better detection of changes that alter behavior

Write your idea clearly and briefly.

A useful improvement is to add a stronger LLM output validation step that checks for both syntax and executable content before accepting a fix. This can be done with a small agent workflow guardrail and an offline regression test, keeping the system reliable without adding much complexity.
