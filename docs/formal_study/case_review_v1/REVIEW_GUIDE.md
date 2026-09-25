# Review guide: essential findings for the 35 new cases

These are preparation materials, not generated reports. Your task is to define the essential content for each case before model responses are available. Existing shared interpretation instructions and rubric v2 remain in effect. No request is made to repeat the previous common-rule review.

## Browser workflow

1. Open `index.html`. Keep its 35 case folders next to it. Read the common guidance at the beginning once.
2. Enter your own reviewer ID and review date, then click **Start / load review**. The two experts must use different IDs and complete their initial reviews independently.
3. Use Case navigation to open a case. Read its actual model input. Expand the supplementary curves and reference context when useful; those plots were not sent to the model.
4. For each candidate, choose **Retain**, **Modify wording**, or **Need not include / Do not adopt**. Do not retain a finding solely because the agent selected a large value. Remove repetitive or unimportant requirements.
5. If modifying, write the full replacement requirement and explain the reason. Specify which components are jointly required (AND), which are alternative ways to convey the finding (OR), and any important partial-coverage boundary. Meaning matters more than literal keywords.
6. Add another essential finding if needed, citing the exact model-visible input. Use the overall case note for unresolved priorities or items requiring discussion.
7. Export **review JSON** and return it to the researcher. This is the editable browser return format. CSV is an optional readable companion; JSON permits resuming on another device. Export incomplete work before stopping, then import it into the master overview to continue.

Browser storage is temporary, not a submitted review and not a change to the source files. The export records whether the review is incomplete and does not claim expert consensus. Do not import the other expert's judgments before completing your independent review.

Each standalone `card.html` embeds its figures and can be reviewed separately. A multi-case JSON belongs in the master overview, which contains all matching case versions. Avoid editing the same case concurrently in multiple tabs. Export before moving to another device or browser.

## Excel alternative

1. Save `Expert_case_requirements_review.xlsx` as a reviewer-specific copy, for example `Expert_case_requirements_review_rater1.xlsx`.
2. Read `Read first`. Use the `Cases` sheet hyperlinks to inspect inputs and figures. Filter `Requirements` by `case_id` to review one case at a time.
3. Use the blue columns: reviewer decision, revised required wording, comments, reviewer and date. Choose **Retain**, **Modify** or **Omit**. Leave the source/evidence columns unchanged.
4. Put additional essential findings in `Additional findings`, with input evidence and component logic. Add rows if necessary.
5. Return the saved workbook. A blank decision is pending; it is not acceptance. Modification without replacement wording is incomplete.

Use either the workbook or browser JSON as your authoritative return. If you also create the other format, identify which one governs so contradictory copies are not silently combined.

## Judgments to keep distinct

- **Required content:** a substantive finding that this report should convey. Retaining a row proposes that requirement; it is not a clinical diagnosis.
- **Optional content:** a supported observation that need not be included. A false optional statement can still be a reporting error.
- **Evidence limits:** follow the already approved rules. Do not require physiological phase labels, unavailable timing references, unsupported clinical severity, or a statement that every healthy measurement is normal.
- **Coverage versus correctness:** a report can cover a fact and contradict it elsewhere; those are recorded separately under the approved rubric. Do not add an unapproved numeric score for partial coverage.

For step-length findings, a direction or rounded-zero interpretation must be supported by the displayed value. Do not require a separate whole-gait disclaimer unless needed to address an actual generalization. For rounded 100% threshold coverage, do not infer absence of brief below-threshold gaps or continuous physiological contraction.

## What this return does not approve

This review does not certify external exposure history, approve a new reference system, define model-comparison power, approve error weights or authorize model generation. It defines proposed new-case requirements within the supplied information. Disagreements will be reconciled after independent returns; retain both original reviews.

## Suggested message to reviewers

Please independently review the prospective requirements for 25 stroke cases and 10 healthy controls. The shared interpretation instructions and rubric have already been confirmed; this round concerns which specific findings are essential in each new case.

Open `index.html` and follow the review controls, or complete a separately saved copy of `Expert_case_requirements_review.xlsx`. Each case includes the exact model input and supplementary curves. Please retain, modify or omit the proposed findings, add any important input-supported omissions, and distinguish required components from optional observations. Numerical ranking is only an agent-generated starting point.

No new model reports are included. Please return your independent JSON export or workbook with your reviewer ID and date. Participant exposure checks remain a separate administrative task, and this review does not authorize a generation batch.
