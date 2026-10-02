# Synthetic Novice Code Research Prototype

A research prototype for generating **functionally correct synthetic CS1 Python submissions** whose observable code-quality defect characteristics are informed by empirical patterns found in authentic novice-programmer submissions.

The prototype combines empirical defect profiling, task-aware LLM prompting, functional validation, structural defect detection, and distribution-based evaluation within a single experimental workflow.

---

## 1. Research Overview

Large language models can generate solutions to introductory programming problems, and previous research has investigated their performance, prompting behaviour, code quality, and ability to generate synthetic programming data (Denny et al., 2023; Finnie-Ansley et al., 2022; Leinonen et al., 2025).

However, generating code that merely appears novice-like is different from generating synthetic code that systematically represents observable characteristics found in authentic novice submissions.

This project investigates whether empirical patterns extracted from authentic CS1 Python submissions can be transformed into task-aware generation constraints and used to guide an LLM toward producing functionally correct synthetic programs with comparable defect distributions.

The research focuses on **observable program characteristics** rather than attempting to reproduce the complete cognitive behaviour of individual novice programmers.

---

## 2. Research Problem

Existing research provides several pieces required for synthetic novice-code generation.

Studies of authentic student programs identify common errors, defects, misconceptions, structural patterns, code-quality characteristics, and semantic-flow characteristics (Denzler et al., 2024; Fwa, 2024; Haindl & Weinberger, 2024; Zhang et al., 2024).

At the same time, research on generative AI demonstrates that LLMs can generate programming solutions and that their outputs can be influenced through prompts, constraints, and interaction strategies (Denny et al., 2023; Kerslake et al., 2024; Leinonen et al., 2025; Pădurean et al., 2025).

Other research evaluates generated or student-written programs through functional testing, code-quality analysis, structural analysis, rubrics, and other forms of automated assessment (Andleeb et al., 2025; Cipriano & Alves, 2023; Pang & Vahid, 2024; Pathak et al., 2025).

These capabilities are useful individually, but the research problem addressed by this project concerns their **integration**.

There is limited work integrating:

1. empirical characteristics of authentic novice code;
2. defect-informed and task-aware generation control;
3. functional validation;
4. structural defect detection; and
5. evaluation of whether synthetic defect distributions correspond to an empirical target.

The prototype is designed to operationalise this integrated process.

---

## 3. Research Gap

> **FIGURE PLACEHOLDER**
>
> `Insert Figure 2 from the research draft here`
>
> **Figure: Research gap identified through the systematic literature review — intersection of Authentic Novice-Code Characteristics, LLM & Generation Prompt Control, and Functional & Defect-Profile Evaluation.**

The figure above positions this research at the intersection of three bodies of knowledge.

### Authentic novice-code characteristics

The first area establishes **what should be represented**.

Research examining authentic novice programs provides empirical evidence about defects, errors, misconceptions, style, quality, structure, semantic flow, and complexity. These characteristics provide candidate observable phenomena for constructing a representation of novice programming behaviour at the source-code level (Denzler et al., 2024; Fwa, 2024; Haindl & Weinberger, 2024; Zhang et al., 2024).

In this project, authentic CS1 Python submissions consequently provide the empirical reference from which selected defect characteristics are identified.

### LLM generation and prompt control

The second area concerns **how the representation can be generated**.

LLMs can produce programming solutions from natural-language descriptions, while prompt design and generation constraints can influence the resulting code (Denny et al., 2023; Finnie-Ansley et al., 2022; Kerslake et al., 2024; Pădurean et al., 2025).

More recent work has also demonstrated the feasibility of producing synthetic buggy programming submissions (Leinonen et al., 2025).

These studies establish that synthetic programming data can be generated, but they do not by themselves establish that the generated code reproduces a specified empirical distribution of novice-code defects.

### Functional and defect-profile evaluation

The third area establishes **how the representation should be evaluated**.

Programming solutions can be evaluated using functional testing as well as code-quality, structural, rubric-based, and defect-oriented analysis (Andleeb et al., 2025; Cipriano & Alves, 2023; Pang & Vahid, 2024; Pathak et al., 2025).

For this research, functional correctness and representational similarity are deliberately treated as separate evaluation dimensions.

A generated submission may contain the intended defect characteristics while failing to solve the original programming problem. Conversely, it may be functionally correct while failing to reproduce the targeted novice-code characteristics.

The prototype therefore evaluates both.

### Central research opportunity

The intersection shown in the figure represents the central research opportunity:

> **to integrate empirical novice-code characteristics, task-aware LLM generation, functional validation, and defect-profile evaluation in order to generate functionally correct synthetic CS1 code whose selected defect characteristics can be evaluated against authentic student data.**

---

## 4. Research Questions

The prototype operationalises three research questions.

### RQ1 — Defect classification

**How can code-quality defect types in authentic CS1 Python submissions be classified as task-independent and task-dependent based on their occurrence patterns across programming tasks?**

This question establishes the empirical foundation of the artefact.

The corresponding objective is to develop a method for distinguishing defects that occur consistently across programming tasks from defects whose occurrence appears associated with particular task characteristics.

---

### RQ2 — Defect-informed generation

**How can empirical profiles of task-independent and task-dependent defects be incorporated into a task-aware prompting approach for generating functionally correct synthetic novice code?**

This question connects empirical analysis with synthetic generation.

The resulting defect profiles are translated into generation constraints that can be incorporated into task-aware prompts supplied to the LLM.

---

### RQ3 — Distribution alignment

**To what extent does iterative, task-aware prompt refinement improve the alignment between the defect distributions of synthetic code and authentic CS1 student submissions compared with a non-adaptive prompting approach?**

This question evaluates the resulting system artefact.

The prototype compares observed defect prevalence in generated submissions with the empirical reference profile while separately monitoring functional correctness.

---

# 5. Research Artefacts

The project produces two closely connected artefacts:

1. a **conceptual artefact**; and
2. a **system artefact**.

---

## 5.1 Conceptual Artefact

The conceptual artefact is a **task-aware defect classification and profiling framework**.

It represents selected observable characteristics of authentic novice Python submissions using:

- defect categories;
- cross-task occurrence patterns;
- task-independent defects;
- task-dependent defects; and
- task-specific empirical defect profiles.

The purpose of the conceptual artefact is not to model every aspect of novice programming behaviour.

Instead, it provides a structured representation of selected observable characteristics that can be operationalised by the generation system.

The conceptual artefact also defines the transformation between:

```text
Authentic submissions
        ↓
Detected defects
        ↓
Cross-task occurrence
        ↓
Task-aware defect profile
        ↓
Generation constraints
```

This transformation connects the empirical component of the research with the synthetic generation component.

---

## 5.2 System Artefact

The system artefact is the executable research prototype contained in this repository.

It operationalises the conceptual artefact through an integrated workflow consisting of:

- authentic-submission analysis;
- functional filtering;
- AST-based defect detection;
- empirical defect-profile construction;
- task-aware prompt construction;
- LLM-based code generation;
- functional validation;
- synthetic defect detection;
- defect-distribution comparison;
- iterative generation/refinement; and
- experimental result analysis.

Rather than introducing an entirely new LLM, testing framework, or program-analysis technology, the contribution of the system artefact lies primarily in **integrating these capabilities into a defect-informed experimental workflow**.

---

# 6. Theoretical Foundation

## 6.1 Representation Theory

Representation Theory provides the primary justificatory theory for the research.

Information systems can be understood as representations of phenomena in a real-world domain, with the usefulness of the representation depending partly on how faithfully the relevant phenomena are represented (Wand & Weber, 1988; Recker et al., 2019).

For this research:

```text
Real-world domain
        │
        ▼
Authentic CS1 Python submissions
        │
        ▼
Observable defect characteristics
        │
        ▼
Conceptual defect profile
        │
        ▼
Generation constraints
        │
        ▼
Synthetic Python submissions
```

Authentic CS1 submissions constitute the empirical domain.

Selected observable defect characteristics are abstracted into the conceptual artefact.

The system artefact then attempts to produce synthetic representations exhibiting corresponding characteristics.

This theoretical perspective motivates evaluating whether the generated representation corresponds to the empirical target.

The prototype consequently measures **defect-category coverage and defect-profile similarity** rather than simply determining whether generated programs look subjectively similar to novice code.

Functional correctness remains a separate criterion because representational similarity alone does not guarantee that a generated program still satisfies its programming-task specification.

---

## 6.2 Design Science Research

Design Science Research provides the overarching research paradigm for constructing and evaluating the artefacts.

DSR centres on the creation and evaluation of purposeful artefacts designed to address identified problems (Hevner et al., 2004).

Within this project:

- the **research problem** motivates the artefact;
- the **systematic literature review** establishes the relevant empirical and methodological knowledge;
- the **system review** identifies technologies capable of operationalising individual parts of the solution;
- the **conceptual artefact** defines what must be represented;
- the **system artefact** implements the representation and generation process; and
- experimental evaluation determines how effectively the resulting artefact addresses the research questions.

Representation Theory and Design Science Research therefore perform complementary roles.

**Representation Theory** explains *what the artefact attempts to represent*.

**Design Science Research** explains *why and how the artefact is constructed and evaluated*.

---

# 7. Prototype Workflow

The complete prototype can be understood as two connected analytical pipelines.

```text
                   AUTHENTIC PIPELINE

Authentic CS1 Python Submissions
                │
                ▼
        Functional Validation
                │
                ▼
 Functionally Correct Submissions
                │
                ▼
        AST Defect Detection
                │
                ▼
     Task-Level Defect Results
                │
                ▼
  Cross-Task Defect Classification
                │
                ▼
   Empirical Target Profiles
                │
                │
                │ guides
                ▼


                   SYNTHETIC PIPELINE

        Task Specification
                +
     Empirical Defect Profile
                │
                ▼
        Prompt Construction
                │
                ▼
          LLM Generation
                │
                ▼
        Functional Validation
                │
                ▼
         Defect Detection
                │
                ▼
   Synthetic Defect Distribution
                │
                ▼
 Authentic ↔ Synthetic Comparison
                │
                ▼
      Iteration / Refinement
```

A key design decision is that the same defect definitions are used when analysing authentic and synthetic code.

This provides a common measurement basis for the distribution comparison.

---

# 8. Authentic Student Baseline

Authentic CS1 Python submissions provide the empirical reference used by the prototype.

Before defect prevalence is calculated, submissions are evaluated for functional correctness so that the empirical target corresponds to programs that satisfy the underlying task specification.

The prototype maps authentic programming questions to prototype task families and then applies the configured defect detectors to eligible submissions.

For a defect \(d\) and task \(t\), the empirical prevalence can be represented conceptually as:

```text
                  submissions containing defect d
P(d | t) = ------------------------------------------------
            eligible functionally correct submissions for t
```

The resulting prevalence values form the target profile used by the generation process.

The intention is not to establish a quota requiring every generated submission to contain a particular defect.

Instead, the target describes the expected **distribution across a collection of generated submissions**.

---

# 9. Task-Aware Defect Profiles

A central aspect of the research is distinguishing between defect characteristics according to their occurrence across programming tasks.

A defect that appears consistently across multiple task families may provide evidence of a relatively task-independent characteristic.

A defect concentrated within particular task families may instead indicate task dependence.

The classification is important because synthetic generation should not assume that every novice-code characteristic occurs with the same probability for every programming problem.

The resulting task-aware profile provides the bridge between RQ1 and RQ2:

```text
Observed authentic behaviour
            ↓
Task-aware classification
            ↓
Empirical defect profile
            ↓
Prompt-level generation constraint
```

---

# 10. Synthetic Code Generation

Synthetic submissions are generated using an LLM provided with:

- the programming-task contract;
- required input/output behaviour;
- structural requirements where applicable; and
- defect-style guidance derived from the empirical target profile.

The current prototype uses **Ollama** as the local model interface. Ollama provides an API and language libraries for interacting with locally deployed language models (Ollama, n.d.).

The generation layer is deliberately separated from the empirical defect-profile layer.

This allows the generation mechanism to change without redefining the underlying research representation.

---

# 11. Functional Validation

Every generated program must first satisfy the programming task.

Functional validation therefore forms an independent gate in the synthetic workflow.

```text
Generated submission
       │
       ▼
Functional tests
   │          │
 PASS       FAIL
   │          │
   ▼          ▼
Analyse    Retry /
defects    regenerate
```

This separation is methodologically important.

A generated program cannot be considered an adequate synthetic representation merely because it contains the desired defect characteristics if it no longer performs the required computation.

Previous research assessing LLM-generated programming solutions also demonstrates the importance of evaluating generated programs beyond textual appearance alone (Cipriano & Alves, 2023; Pang & Vahid, 2024).

---

# 12. Defect Detection

The prototype uses structural source-code analysis to identify configured code characteristics.

Python's Abstract Syntax Tree functionality provides a programmatic representation of Python source-code structure and enables the prototype to inspect syntactic constructs without relying only on raw text matching (Python Software Foundation, n.d.).

The detector registry is shared between the authentic and synthetic analysis pipelines:

```text
Authentic Code ──────┐
                     │
                     ▼
              Shared Detectors
                     ▲
                     │
Synthetic Code ──────┘
```

Using a shared measurement process helps ensure that differences observed between the two distributions do not arise simply from applying different defect definitions.

---

# 13. Evaluation Strategy

The prototype evaluates the generated data along two principal dimensions.

## 13.1 Functional correctness

The first criterion determines whether generated submissions continue to satisfy the original programming-task requirements.

Possible metrics include:

- generated submissions;
- functionally correct submissions;
- functional success rate; and
- generation retries.

---

## 13.2 Defect-profile alignment

The second criterion evaluates whether the observed synthetic defect distribution corresponds to the empirical authentic distribution.

For each defect:

```text
Authentic target prevalence
             ↕
Synthetic observed prevalence
```

The comparison can be performed:

- by defect;
- by task;
- by iteration; and
- across the prototype as a whole where appropriate.

Because synthetic batches represent samples rather than deterministic reproductions of the authentic population, differences should be interpreted together with sampling uncertainty rather than assuming that exact equality is required.

---

# 14. Iterative Refinement

The prototype supports repeated generation and evaluation.

Conceptually:

```text
Target profile
      ↓
Prompt
      ↓
Generate
      ↓
Validate
      ↓
Detect
      ↓
Compare
      ↓
Refine
      └──────────→ next iteration
```

This iterative mechanism provides the experimental basis for RQ3.

A non-adaptive generation configuration can provide a baseline against which the behaviour of task-aware iterative refinement is compared.

The research question is not simply whether an LLM can generate code.

Instead, it investigates whether an adaptive, empirically informed process changes the correspondence between the synthetic and authentic defect distributions while retaining functional correctness.

---

# 15. Prototype Interface

The Streamlit application provides an interactive interface to the research artefact.

The main application areas include:

### Home

Provides an overview of the research problem, artefacts, prototype workflow, empirical reference data, and implementation status.

### Generation

Runs the synthetic-code generation workflow using a selected prototype task and configured generation parameters.

This component is responsible for:

```text
Target Profile
     ↓
Prompt Construction
     ↓
LLM Generation
     ↓
Functional Validation
     ↓
Defect Analysis
```

### Defect Detection

Provides access to the defect-analysis component used to evaluate code according to the prototype's configured structural defect definitions.

### Evaluation and Analytics

Generation results can be analysed at the submission, defect, task, and iteration levels.

The evaluation layer connects the generated outputs back to the authentic empirical baseline.

---

# 16. Prototype Tasks

The current prototype uses three representative programming-task families.

```text
T1 — [Task name / family]
T2 — [Task name / family]
T3 — [Task name / family]
```

Each prototype task is associated with:

- a task contract;
- mapped authentic programming questions;
- eligible authentic submissions;
- a task-specific defect profile;
- generation constraints;
- functional tests; and
- synthetic evaluation results.

> Replace the placeholders above with the final names and task descriptions used in the implementation.

---

# 17. System Components

At a high level, the prototype contains the following components.

| Component | Purpose |
|---|---|
| Authentic dataset layer | Provides the empirical CS1 submission data |
| Task mapping | Maps authentic exercises to prototype task families |
| Functional validator | Identifies functionally correct submissions |
| Defect detector registry | Detects configured structural/code-quality characteristics |
| Profile builder | Constructs empirical task-aware defect targets |
| Prompt builder | Translates target characteristics into generation constraints |
| LLM interface | Generates synthetic Python submissions |
| Synthetic validator | Ensures generated programs remain functionally correct |
| Comparison engine | Compares authentic and synthetic defect prevalence |
| Analytics layer | Presents task-, defect-, and iteration-level results |
| Export layer | Preserves generated programs and experimental outputs |

Together these components implement the system artefact defined by the research design.

---

# 18. What This Prototype Does Not Claim

The prototype does **not** attempt to:

- reproduce a particular student's program;
- model the complete cognitive process of novice programmers;
- claim that a detected source-code characteristic uniquely identifies a human novice;
- require every synthetic submission to contain the same defects;
- treat functional correctness and representational similarity as equivalent; or
- establish that the current detector set captures every possible novice programming characteristic.

Instead, the project investigates whether selected **observable defect characteristics** can be empirically represented and reproduced at the distribution level through controlled synthetic generation.

---

# 19. Current Research Scope

Implemented or represented within the current prototype:

- authentic CS1 submission analysis;
- functional correctness filtering;
- task-aware authentic baseline construction;
- AST-based defect detection;
- synthetic Python generation;
- task-specific prompting;
- functional validation;
- defect-prevalence measurement;
- authentic-versus-synthetic comparison;
- iterative generation; and
- experiment result export and analysis.

Areas requiring further evaluation include detector validity, larger fixed-configuration experiments, and final comparison of adaptive and non-adaptive generation conditions.

---

# 20. Research Contribution

The intended contribution is not simply another interface for generating Python programs with an LLM.

The research contribution lies in connecting four stages that are commonly treated separately:

```text
EMPIRICAL OBSERVATION
        ↓
REPRESENTATION
        ↓
CONTROLLED GENERATION
        ↓
EMPIRICAL EVALUATION
```

Authentic novice-code characteristics provide the empirical observation.

The task-aware defect profile provides the conceptual representation.

Prompt constraints operationalise the representation during generation.

Functional and defect-distribution evaluation assess the resulting synthetic representation.

This produces a traceable connection between **what is observed in authentic student code**, **what is represented by the artefact**, **what the LLM is instructed to generate**, and **how the synthetic output is evaluated**.

---

# 21. Repository Structure

```text
project/
│
├── app.py
├── home.py
│
├── app_pages/
│   ├── generation.py
│   └── defect_detection.py
│
├── [detectors/]
│   └── ...
│
├── [generation/]
│   └── ...
│
├── [validation/]
│   └── ...
│
├── [data/]
│   └── ...
│
├── [results/]
│   └── ...
│
└── README.md
```

> Update this section using the final repository structure.

---

# 22. Running the Prototype

```bash
# Install project dependencies
pip install -r requirements.txt

# Start the Streamlit application
streamlit run app.py
```

The Ollama service and the model configured by the experiment must also be available when running local synthetic generation.

> Replace these instructions with the final installation and configuration procedure used by the repository.

---

# 23. Research Status

This repository contains a **research prototype**.

Results generated through the interface should therefore be interpreted as experimental outputs rather than as evidence of a completed benchmark until the final fixed-configuration evaluation has been conducted.

---

# References

Andleeb, S., Kantorski, B., & Carver, J. (2025). ChatGPT in Introductory Programming: Counterbalanced Evaluation of Code Quality, Conceptual Learning, and Student Perceptions. *Proceedings of the 26th ACM Annual Conference on Cybersecurity & Information Technology Education*, 180–186. https://doi.org/10.1145/3769694.3771128

Cipriano, B. P., & Alves, P. (2023). GPT-3 vs Object Oriented Programming Assignments: An Experience Report. *Proceedings of the 2023 Conference on Innovation and Technology in Computer Science Education V. 1*, 61–67. https://doi.org/10.1145/3587102.3588814

Denny, P., Kumar, V., & Giacaman, N. (2023). Conversing with Copilot: Exploring Prompt Engineering for Solving CS1 Problems Using Natural Language. *Proceedings of the 54th ACM Technical Symposium on Computer Science Education V. 1*, 1136–1142. https://doi.org/10.1145/3545945.3569823

Denzler, B., Vahid, F., Pang, A., & Salloum, M. (2024). Style Anomalies Can Suggest Cheating in CS1 Programs. *Proceedings of the 2024 Conference on Innovation and Technology in Computer Science Education V. 1*, 381–387. https://doi.org/10.1145/3649217.3653626

Finnie-Ansley, J., Denny, P., Becker, B. A., Luxton-Reilly, A., & Prather, J. (2022). The Robots Are Coming: Exploring the Implications of OpenAI Codex on Introductory Programming. *Proceedings of the 24th Australasian Computing Education Conference*, 10–19. https://doi.org/10.1145/3511861.3511863

Fwa, H. L. (2024). Experience Report: Identifying common misconceptions and errors of novice programmers with ChatGPT. *Proceedings of the 46th International Conference on Software Engineering: Software Engineering Education and Training*, 233–241. https://doi.org/10.1145/3639474.3640059

Haindl, P., & Weinberger, G. (2024). Does ChatGPT Help Novice Programmers Write Better Code? Results From Static Code Analysis. *IEEE Access, 12*, 114146–114156. https://doi.org/10.1109/ACCESS.2024.3445432

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly, 28*(1), 75–105. https://doi.org/10.2307/25148625

Kerslake, C., Denny, P., Smith, D. H., Prather, J., Leinonen, J., Luxton-Reilly, A., & MacNeil, S. (2024). Integrating Natural Language Prompting Tasks in Introductory Programming Courses. *Proceedings of the 2024 ACM Virtual Global Computing Education Conference V. 1*, 88–94. https://doi.org/10.1145/3649165.3690125

Leinonen, J., Denny, P., Kiljunen, O., MacNeil, S., Sarsa, S., & Hellas, A. (2025). LLM-itation is the Sincerest Form of Data: Generating Synthetic Buggy Code Submissions for Computing Education. *Proceedings of the 27th Australasian Computing Education Conference*, 56–63. https://doi.org/10.1145/3716640.3716647

Ollama. (n.d.). *Introduction*. https://docs.ollama.com/api/introduction

Pang, A., & Vahid, F. (2024). ChatGPT and Cheat Detection in CS1 Using a Program Autograding System. *Proceedings of the 2024 Conference on Innovation and Technology in Computer Science Education V. 1*, 367–373. https://doi.org/10.1145/3649217.3653558

Pathak, A., Gandhi, R., Uttam, V., et al. (2025). Rubric Is All You Need: Improving LLM-Based Code Evaluation With Question-Specific Rubrics. *Proceedings of the 2025 ACM Conference on International Computing Education Research V.1*, 181–195. https://doi.org/10.1145/3702652.3744220

Python Software Foundation. (n.d.). *ast — Abstract syntax trees*. https://docs.python.org/3/library/ast.html

Recker, J., Indulska, M., Green, P. F., Burton-Jones, A., & Weber, R. (2019). Information systems as representations: A review of the theory and evidence. *Journal of the Association for Information Systems, 20*(6), 735–786. https://doi.org/10.17705/1jais.00550

Wand, Y., & Weber, R. (1988). An ontological analysis of some fundamental information systems concepts. *Proceedings of the International Conference on Information Systems*.

Zhang, A. G., Tang, X., Oney, S., & Chen, Y. (2024). CFlow: Supporting Semantic Flow Analysis of Students' Code in Programming Problems at Scale. *Proceedings of the Eleventh ACM Conference on Learning @ Scale*, 188–199. https://doi.org/10.1145/3657604.3662025