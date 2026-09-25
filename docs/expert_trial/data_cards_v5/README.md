# Draft data cards for 5 cases

Open index.html to browse and interactively review all cases (figures and review functions are embedded and available offline). Each case's card.html can be shared separately.
Review the common review section at the beginning only once; the export includes common_rules and the five case sections; common_rules is not a sixth participant.
Single-case pages also include the same version of the common section for standalone use.
First enter your expert ID and click “Start／load review”, then accept/modify/delete items individually and add items.
When finished, export the JSON and return it to the researcher; CSV can be viewed in Excel, and JSON allows completion to resume across devices. Different experts should use different IDs.
Temporary browser storage is not formal submission and does not modify the original files on disk; be sure to export.
Each case also provides PNG/PDF figures, model_system_prompt.txt, model_user_prompt.txt, model_messages.json,
summary.json, facts.json, reference_card.md, checklist_DRAFT.md, and an expert-editable CSV.

These are expert preparation materials, with no model reports, model identities, or answer key. Experts first review and finalize the checklists, then blinded rating begins.
Do not directly use candidate “must describe” items as deduction criteria; do not deduct points because the model did not mention expert supplementary figures or detailed percentiles
that were not provided. When checking values, consider the display precision of the model input; do not hold the model accountable to full machine precision.

The model input snapshot uses the same function as the current formal entry point; any subsequent prompt/data changes should trigger regeneration as a new version,
and the system_prompt/user_prompt saved in the actual reports should be checked rather than assumed to remain identical forever.
Healthy Sub49 uses a 137-person reference excluding this participant, with the valid n for each muscle listed separately; the empirical calibration distribution and reference membership for this case are not the same concept.
This project evaluates only report faithfulness and interpretive boundaries given the evidence provided; it does not validate diagnosis or treatment.

Example generation command:
`python scripts/build_expert_trial_package.py --verified-cache --out docs/expert_trial/data_cards_vNEXT`
Alternatively, omit --verified-cache to read the released Excel/MAT directly. Existing directories are not overwritten, to preserve expert edits.
manifest.json records the sources, source code, and hashes of all deliverables; the cache is not in Git, so local data are required or direct reading must be selected.
