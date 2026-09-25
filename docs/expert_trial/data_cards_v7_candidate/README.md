# Five-case draft data cards

Open index.html to browse and interactively review all cases (plots and review tools are embedded for offline use). Each card.html can be shared separately.
Review the common section at the front only once; exports contain common_rules and the five case sections. common_rules is not a sixth participant.
Individual case pages also include the same common section for standalone use.
First enter your reviewer ID and click "Start / load review," then accept/edit/delete items and add new ones.
When finished, export JSON and return it to the researcher; CSV can be viewed in Excel, and JSON supports resuming across devices. Different experts must use different IDs.
Browser storage is not a formal submission and does not modify original files on disk; be sure to export.
Each case also provides PNG/PDF plots, model_system_prompt.txt, model_user_prompt.txt, model_messages.json,
summary.json, facts.json, reference_card.md, checklist_DRAFT.md, and an expert-editable CSV.

These are expert preparation materials, without model reports, model identities, or an answer key. Have experts approve the checklist before blinded rating.
Do not directly use candidate "Must describe" items as penalty criteria; do not penalize models for omitting supplementary expert plots or detailed percentiles
not supplied to them. Consider the display precision of the model input when checking numbers; do not hold models to full machine precision.

Model-input snapshots use the selected prompt version. The candidate version is opt-in and is not yet the approved formal generation route. Any subsequent prompt/data change requires a new version,
with checks against the system_prompt/user_prompt saved in the actual reports rather than an assumption of perpetual consistency.
Healthy Sub49 uses a 137-person reference excluding that participant; valid n is listed separately for each muscle. Empirical calibration distributions and case-specific reference membership are distinct concepts.
This project evaluates only report fidelity and interpretation boundaries under the supplied evidence; it does not validate diagnosis or treatment.

Example generation command:
`python scripts/build_expert_trial_package.py --verified-cache --prompt-version limited-evidence-v3.1-candidate --out docs/expert_trial/data_cards_vNEXT`
Alternatively, omit --verified-cache to read the released Excel/MAT directly. Existing directories are not overwritten, preserving expert edits.
manifest.json records source, code, and all deliverable hashes; the cache is not in Git, so local data or direct reading is required.
