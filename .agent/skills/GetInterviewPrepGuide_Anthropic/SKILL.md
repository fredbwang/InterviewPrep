---
name: GetInterviewPrepGuide_Anthropic
description: Process new interview questions for Anthropic
---

# GetInterviewPrepGuide_Anthropic

This skill processes new interview questions, creating a dedicated folder for each question with preparation materials.

## Steps

1.  **Understand the Question**: 
    - Identify the core problem name (e.g., "StackToTrace", "FileDedup").
    - Identify the category (Coding, System Design, Behavioral).

2.  **Create Directory**:
    - Path: `c:/Users/Fred/Coding/python/anthropic/<Category>/<QuestionName>/`
    - Verify if it exists; if not, create it.

3.  **Generate Content**:
    - Create a `README.md` inside that folder.
    - Include: Problem statement, Example, detailed Solution Logic (or stub), and Complexity/Constraints.
    - Create a `solution` file (e.g., `solution.py`) if code is applicable.

4.  **Update Tracker**:
    - File: `c:/Users/Fred/Coding/python/anthropic/question_frequency.md`
    - Add/Update row:
      | Question | Classification | Frequency | Local Material | Source |
      | :--- | :--- | :---: | :--- | :--- |
      | **<QuestionName>** | <QType> | <Count> | [Folder](<RelPath>) | [Source](...) |

5.  **Classification**:
    - Use `c:/Users/Fred/Coding/python/anthropic/Anthropic_Interview_Guideline.md` to determine `<QType>` (e.g., Coding Q1).

## Execution

(The agent should perform these steps manually or script them when invoking this skill)
