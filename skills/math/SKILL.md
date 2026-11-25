---
name: math
description: >-
  Solve, verify, and explain mathematical problems using
  rigorous reasoning, exact computation, and appropriate
  numerical methods. Use for arithmetic, algebra, geometry,
  calculus, linear algebra, discrete mathematics, probability,
  statistics, optimization, proofs, and mathematical modeling.
  Also use to check equations, derivations, and numerical claims.
---

# Mathematics

## Objective

Produce mathematically correct, verifiable solutions with
the least necessary complexity. Prioritize correctness over
speed, elegance, or confidence.

## Principles

- Distinguish given facts, assumptions, definitions, and conclusions.
- Prefer exact symbolic results when practical; approximate only when useful or necessary.
- Preserve domains, units, signs, constraints, and dependencies throughout calculations.
- Choose the simplest valid method that fits the problem.
- Never invent a theorem, computation, proof, or verification result.
- Do not change a valid conclusion merely to agree with an expected answer.

## Workflow

1. **Understand.** Identify the requested result, known quantities,
   unknowns, domains, and constraints. Resolve material ambiguities
   or state the assumptions used.

2. **Formalize.** Translate the problem into equations, definitions,
   inequalities, or logical statements. Introduce notation only
   when useful.

3. **Select a method.** Consider direct computation, symbolic
   manipulation, a relevant theorem, numerical methods, or
   a constructive proof. Avoid unnecessary search or brute force.

4. **Solve.** Carry out valid transformations and computations.
   Track conditions under which each transformation holds,
   and preserve intermediate precision.

5. **Verify.** Check the candidate result against the original
   problem. For nontrivial results, use an independent check
   when practical. Investigate discrepancies rather than
   ignoring them.

6. **Present.** State the result clearly with the necessary
   derivation, assumptions, units, and limitations. Match the
   depth of explanation to the request.

## Computation

- Use available calculators, Python, or symbolic mathematics tools for error-prone calculations, numerical analysis, or independent verification when appropriate.
- Use exact integers, rational numbers, and symbolic expressions where practical.
- Round only at the final step unless the numerical method requires otherwise.
- For numerical methods, consider convergence, stability, precision, conditioning, and error bounds when relevant.
- Distinguish exact equality from approximation.
- Never claim a tool was executed unless it was actually used.

## Proofs

- State the proposition, assumptions, and applicable domain precisely.
- Check the hypotheses of every theorem used.
- Choose an appropriate proof technique: direct proof, contradiction, induction, contrapositive, construction, or exhaustive cases when justified.
- Justify nontrivial logical transitions and cover all required cases.
- Distinguish necessary conditions from sufficient conditions.
- A numerical example may illustrate or disprove a universal claim, but successful examples alone do not establish a proof.
- If a proof cannot be completed, identify the unresolved step rather than presenting an incomplete argument as established.

## Common failure modes

Check for relevant issues rather than applying every check mechanically:

- Division by zero, invalid domains, and lost or extraneous solutions.
- Sign errors, incorrect inequality reversal, and invalid cancellation.
- Missing constants, boundary conditions, endpoints, and degenerate cases.
- Unjustified independence assumptions or incorrect conditional probabilities.
- Confusing correlation with causation, sample statistics with population parameters, or statistical significance with effect size.
- Premature rounding, floating-point cancellation, overflow, and ill-conditioned computation.
- Confusing local and global optima or claiming uniqueness without justification.
- Circular reasoning, invalid quantifiers, and unproven assumptions.

## Verification

Choose checks suited to the result:

- Substitute solutions into the original equations and constraints.
- Check dimensions, units, signs, magnitude, and limiting behavior.
- Test boundary cases and seek counterexamples to general claims.
- Compare against a separate derivation or computational method when practical.
- For optimization, check feasibility and the conditions required for the claimed optimum.
- For approximate answers, assess residuals and numerical error where meaningful.

If verification fails, revisit the derivation and correct the
underlying error before reporting a result. If uncertainty
remains, state what is established and what is not.

## Output

- Give the requested result clearly, with exact and approximate forms when useful.
- Include enough mathematical justification to make the result independently checkable.
- Use conventional mathematical notation and define unfamiliar symbols.
- Explain assumptions and meaningful limitations without unnecessary narration.
- For simple calculations, keep the response short. For proofs and complex problems, provide the required detail.

## Completion criteria

A solution is complete when the requested quantities or claims
have been addressed, the reasoning is valid, the original
constraints are satisfied, and any remaining uncertainty or
approximation is disclosed.

Do not claim completeness when these conditions are not met.
