# NDA Contract Risk Review Tool

**Application URL:**  
https://eb8yddrkxltugxojl4dyhi.streamlit.app/

---

## 1. Purpose of the Application

This web application provides a **rapid, clause-level legal risk screening** for standard Non-Disclosure Agreements (NDAs).  
It is designed for **preliminary review** scenarios—where a lawyer or analyst needs to quickly identify **major structural risks** or **non-compliant confidentiality terms**, before conducting detailed legal drafting or negotiation.

This tool does **not** replace full legal analysis. Instead, it assists with early-stage review by applying a set of **structured SOP rules** that reflect common NDA risk patterns (e.g., confidentiality duration issues, over-broad definitions, subjective duty of care clauses).

---

## 2. System Structure (Brief Architectural Summary)

System Architecture (Concise)

The application operates in three layers:

1. SOP Rule Engine (sop_analyzer.py)
	•	A deterministic rule-based system (no free-form AI decision-making).
	•	Identifies clause type (e.g., Definition / Use / Term).
	•	Flags risk patterns such as:
	•	Overbroad definitions
	•	Subjective standards (“reasonable efforts”)
	•	Fixed-term protection applied to trade secrets
	•	Outputs: Red / Yellow / Green + explanation + suggested revision.

2. Reference Clause Database
	•	Contains several standard NDA clause examples.
	•	Used only as supplementary grounding to avoid hallucinated phrasing.
	•	Does not determine risk — it supports tone and consistency.

3. Explanation Refinement (explainLLM.py)
	•	Rewrites the explanation in concise legal language.
	•	Keeps the logic and conclusions unchanged.

⸻

Workflow
	1.	User uploads document.
	2.	Text is extracted and split into clauses.
	3.	SOP Engine classifies risks.
	4.	Explanations are refined for clarity.
	5.	Results are displayed + downloadable report is generated.

⸻

Capabilities
	•	Detects major NDA drafting risks quickly.
	•	Produces structured clause-by-clause analysis.
	•	Generates a clean legal-format report.

Limitations
	•	Designed for standard NDAs.
	•	Does not replace full legal review.
	•	Database provides reference, not authority.


## 3. How to Use the Application

1. Open the deployed web URL.  
2. Enter your OpenAI API key in the left sidebar.  
3. Upload an NDA contract (`.pdf`, `.docx`, or `.txt`).  
4. The system will:
   - Extract and split the contract text into clauses
   - Apply SOP rule analysis to determine risk category
   - Display results in the UI
   - Provide a **downloadable formal review report (.docx)**

---

## 4. Test Cases

To demonstrate correctness and repeatability, three NDA samples were used.  
These files are included in the repository under `/tests/`:


**Test1

CONFIDENTIALITY AGREEMENT

1. Definitions
"Confidential Information" means **all information disclosed in any manner**, without exception. Oral information is covered only if it is marked as confidential in writing prior to disclosure.

2. Term
The confidentiality obligations shall apply **for a period of 3 years** from the date of disclosure, **including Trade Secrets**.

3. Use and Obligations
The Receiving Party shall use reasonable efforts to protect the Confidential Information.

4. Governing Law
This Agreement is governed by the laws of the State of California.

**Test2

MUTUAL NON-DISCLOSURE AGREEMENT

1. Confidential Information
Confidential Information includes written or oral information disclosed in relation to discussions between the parties. However, information must be **marked as Confidential** to be protected.

2. Purpose
The Receiving Party may only use the information to evaluate a potential business transaction.

3. Obligations
The Receiving Party shall protect the Confidential Information using commercially reasonable efforts.

4. Term and Survival
The confidentiality obligations shall remain in effect for **5 years** from disclosure. Trade secrets are not mentioned.

5. Entire Agreement
This Agreement constitutes the entire agreement between the parties.

**Test 3
NONDISCLOSURE AGREEMENT (NDA)

1. Definition of Confidential Information
Confidential Information includes: 
(a) written information marked as "Confidential", 
(b) oral information identified as confidential at the time of disclosure and confirmed in writing within 5 business days.
Confidential Information excludes information already public, independently developed, or lawfully obtained from a third party.

2. Use Restriction
Receiving Party shall use the Confidential Information solely for evaluating the Business Purpose.

3. Protection of Information
Receiving Party shall protect the information with the same care it uses for its own confidential information, and not less than a reasonable standard of care.

4. Duration
Confidential Information shall be protected for 5 years. 
Notwithstanding the foregoing, **Trade Secrets shall be protected indefinitely**, until they no longer qualify as Trade Secrets.

5. Governing Law
This agreement is governed by the laws of Singapore.

The three text-based NDA samples (Test1, Test2, Test3) are used because they allow the web application to demonstrate its core functionality quickly and clearly:
	•	Clause Extraction – the system correctly separates numbered clauses into analyzable units.
	•	Rule-Based Risk Classification – each clause is labelled Red / Yellow / Green based on predefined SOP risk criteria.
	•	Legal Reasoning Output – for each flagged clause, the system provides a short rationale and a suggested revision.

These tests run instantly and are easy to replicate, ensuring the evaluation is transparent and consistent.

Optional Additional Test Documents (PDF Format)

The following two longer NDA PDFs may also be uploaded to test performance on more complex formatting:

  https://www.tntech.edu/research/pdf/researchcompliance/NDA_Mutual_template2_5_2019.pdf

  https://assets.publishing.service.gov.uk/media/5a8188fd40f0b62302697d5e/Example-Mutual-Non-Disclosure-Agreement.pdf

However, because I used a fixed process to limit the reasoning ability of the model in order to ensure the authenticity of the answers, the answers it detected might still be very random and limited.

### To Run the Tests:
1. Upload each test file individually through the UI
2. Compare detected risk summary:
   - **Red** → High legal risk in confidentiality duration terms
   - **Yellow** → Ambiguity / enforceability caution
   - **Green** → Clause structure aligns with common industry practice

This demonstrates **consistent rule-based evaluation**, which is one of the key objectives of the assignment.

---

## 5. Output Report Example

The generated report includes:

- Clause numbering and titles
- Original clause excerpt
- Risk classification (Red / Yellow / Green)
- Explanation of why the clause was assigned that classification
- Recommended drafting revisions (where applicable)

This format is suitable for:
- Internal legal team review
- Early-stage negotiation preparation
- Training junior analysts

---

## 6. Limitations (Explicit but Professional)

- The tool does not interpret *business context* or *transaction intent*.
- No jurisdiction-specific case-law reasoning is performed.
- It serves as **a structured screening layer**, not full legal advice.

This is done to ensure the utmost authenticity of the responses, in order to avoid obtaining fabricated answers and fabricated laws.

## 7. Conclusion

This application demonstrates:
- The ability to ingest and process uploaded legal documents
- Structured automated issue detection
- Meaningful summarisation in professional report format
- And repeatability through testable, rule-based logic

It fulfills the task objective of **“rapidly reviewing documentary evidence for legal risks”**, within the scope of NDA confidentiality evaluation.
