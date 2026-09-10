# Mechanism-triggered validation

Use only sections whose mechanism can change the current answer. Start from the official subquestion, its explicit simplifications and derived necessary conditions; a contest label or method keyword is not a trigger. These are risk prompts, not mandatory experiments or automatic model upgrades.

Put the selected falsifiable condition in the existing `verification_plan` and, when useful, `model/VALIDATION_PLAN.md`: identify the quantity, scope, units, failure condition and tolerance basis. Tolerances follow measurement resolution, numerical error and the decision margin; there is no universal cutoff. Reuse evidence only when its inputs, implementation, check definition and scope still match. Reading this guide or naming an assertion is not verification. Computable checks must inspect actual results and be written by the executed program through `--assert-file`; mathematical applicability and proof strength remain reviewer judgments. Writing and compilation consume the reviewed evidence rather than starting these experiments again.

## Continuous events and first arrival

**When:** the answer depends on a continuous trajectory crossing, touching or staying outside a boundary.

Endpoint safety does not establish interval safety. Sign-change searches can miss tangent roots or multiple crossings within one step. Check event direction, an initially satisfied condition and ordering of competing events. Refine critical intervals or use derivative/interval bounds; denser printed output alone does not improve the integrator. A finite scan without a root is not a proof of no event.

**Discriminating check:** for contact defined by `g(t) <= 0`, `g(t) = (t - 0.5)^2` on `[0, 1]` touches at `0.5` although both endpoints are positive. Check the stationary point as well as endpoints. Use problem-specific error bounds for a numerical trajectory.

**Boundary:** a task defined only at discrete observation times needs no continuous interpolation guarantee. If contact requires strict penetration, this tangent alone is not penetration.

## Inverse problems and calibration

**When:** observations determine unknown parameters or a simplified forward model is inverted.

Reconstruct the corresponding observations with the fitted parameters and original units/domain. Small residuals do not imply unique parameters: inspect scaled sensitivities/Jacobian rank, profiles or alternative parameter combinations where uniqueness matters. Shared-object measurements must use consistent shared parameters unless the task supplies state differences. Separate noise, discretization and approximation error; fitting data are not independent validation.

**Boundary:** non-identifiable parameters do not automatically invalidate an identifiable prediction. Preserve the requested approximation and report its domain; do not force uniqueness with invented bounds or replace the requested model merely because a richer fit is possible.

## Sequential sampling and reliability boundaries

**When:** simulation or sampling decides reliability, minimum capacity or a stopping threshold.

Define the probability event and sampling unit. An interval crossing the target leaves the decision undecided. Repeatedly inspecting fixed-sample intervals and stopping on success does not preserve nominal coverage. Use a prespecified validation design or a sequential guarantee whose assumptions match; validate an optimized candidate independently or account for selection. Check monotonicity before binary search and distinguish feasible, infeasible and unresolved boundary candidates when the budget ends.

**Boundary:** a truly fixed validation sample does not require sequential machinery. Shared random numbers can help paired comparisons, but identical repeats are not independent sample size. Neither a universal sample count nor a forced pass/fail verdict is justified.

## Discrete optimization and exported plans

**When:** the answer is a schedule, allocation, route, layout or rounded/postprocessed optimization result.

Read the final exported plan and independently recompute its objective and applicable resource, timing, integrality and terminal constraints from the original definition. Solver status describes the internal solve: distinguish incumbent feasibility, valid bound, stopping reason and claimed optimality. A timeout is not infeasibility, and successful exit is not global optimality. Report violations with the affected object, time/resource, observed value and requirement.

**Discriminating check:** the relaxation `x = y = 0.6` satisfies `x + y <= 1.2`; rounding each variable to one violates it. Replay the exported integers, not the retained relaxation. A repaired feasible plan still needs its own objective and optimality scope.

**Boundary:** do not impose integrality on genuinely divisible decisions, full service where omissions carry a permitted penalty, or rest/setup rules absent from the task. Back-to-back half-open intervals are compatible when no additional gap is required.

## Objective priority and available information

**When:** objectives have an explicit priority or questions/policies have different information sets.

Map the current question to variables, objective order and observations available at each decision. Lexicographic optimization is not an arbitrary weighted sum: establish bounds and weight dominance for an equivalent encoding, or preserve preceding objectives with justified tolerances in sequential solves. An unproved first-stage optimum cannot support a claim of overall lexicographic optimality. Simulated future weather/demand/failures may be known to the world generator but unavailable to the policy.

**Boundary:** a mathematically equivalent formulation is valid despite a different method name. An explicitly labeled omniscient benchmark is permissible; it is not an executable policy. Do not import later-question information or old-contest constants into this question.

## Dynamics and physical quantities

**When:** constitutive laws, evolving stocks, accumulated output or time averages drive the answer.

Distinguish coefficient, force and power: for a passive damper with relative velocity `u` and nonnegative coefficient `c(u)`, a consistent convention gives `F = -c(u)u` and dissipated power `-Fu = c(u)u^2`. Check sign, units and relevant zero/limit cases. Recompute state balances and the objective from the trajectory: stock differs from flow, an integral differs from an average, and unequal time spacing generally requires time weights. Apply the specified transient window and terminal/periodic conditions. For discretized fields, solver residual, grid/time/domain error and model error are distinct; test the answer quantity where those errors could change it.

**Boundary:** active energy input is not passive dissipation; an open system needs the correct flux balance, not forced constant energy. A finite-horizon task does not automatically require a steady-state simulation or invented terminal penalty.

## Grouped data and surrogate optimization

**When:** repeated records share an object/batch/trajectory, or a fitted predictor selects a decision.

Choose the experimental unit and split to match deployment. Fit imputation, scaling, feature selection and tuning inside the appropriate training folds. Check feature availability at prediction time. Single-factor data do not automatically identify interactions; inspect estimable effects when interpreting parameters. For surrogate optima, check support domain, feasible controls and the final candidate against the original physical definition or independent observations; high training fit alone cannot validate an extremum or intervention benefit.

**Discriminating check:** for prediction on unseen objects, intersect the object IDs in train and test; row-disjoint sets may still share every object. Preserve the offending IDs as diagnostic evidence.

**Boundary:** predicting future records for known objects can permit shared IDs if temporal and feature availability constraints are respected. Low rank limits particular parameter interpretations, not every prediction. Without candidate validation, report an unverified prediction rather than fabricating experimental confirmation.
