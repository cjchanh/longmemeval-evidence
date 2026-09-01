---
content:
  personal: false
  operator_pii: false
  framework_internal: false
  public_shippable: true
  ops_log: false
  third_party_identifiable: false
  may_dispatch_to_cloud: true
  contains_named_entities: []
privacy: no personal or corpus data leaves the machine; payloads are (question, gold, response) triples from the PUBLIC LongMemEval benchmark plus the frozen judge rubric; the only secret is the operator-supplied OpenAI API key at ~/.config/openai/api_key (0600), sent solely as the Authorization header to api.openai.com, never logged or echoed
---
# Dispatch spec — GPT-4o judge rescore (cloud egress classification)

- Destination: api.openai.com (GET /v1/models probe; chat completions, model gpt-4o).
- Operator authorization: in-session, verbatim ("I have a key copied paste dont look and run", 2026-08-30), recorded in ~/.claude/resolutions/EGRESS_20260831_gpt4o_judge.json.
- Commands covered: model-availability probe and python3 scripts/rescore_gpt4o_judge.py --transport api over the frozen reader checkpoints.
- Spend bound: <= ~1,100 judge calls (500-row run x2 + controls); est. $5-15 total.
