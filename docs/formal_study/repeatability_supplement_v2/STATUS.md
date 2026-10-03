# Generation complete

All 150 amended slots have been processed and exported: 50 per model, 75 per wave, two new responses per case/model. With the original stroke reports, there are three response records per case/model. The original 30 control reports are unchanged.

Of the new captures, 149 ended normally and one retains only partial text from the study-lead pause (Sub22, OpenAI, wave 1). That operational interruption is preserved and flagged, not replaced or counted as a complete report. There were no retries, no token-limit finishes and no third-wave dispatches. The runner has exited successfully.

GENERATION_COMPLETION.json records the final journal identity, results hash and 150 report-file hashes. GENERATION_STATUS.json is the final technical snapshot. Raw evidence, RESULTS.json and captured_reports remain under data/reports_repeatability_v1. Exact inputs and generation settings remain registered in EXECUTION_PLAN.json.

Technical completion is not expert scoring or clinical validation. Three independent review packets are ready under ../repeatability_rating_delivery_v2, each with 150 verbatim texts, exact inputs, verified reference assets, 864 blank coverage rows, current rules and a reviewer exposure form. Eight delivery/import checks passed. Each named ZIP is self-contained; model/repeat mappings remain outside the delivery folder. Nothing has been sent. Next distribute the corresponding named ZIP to each reviewer and collect their independent completed workbooks. Preserve the incomplete-capture flag in administrative records and apply the stated complete-capture and all-planned analyses. No additional live generation is currently authorized.
