# Eval results

**Action accuracy: 19/20 (95%)**  |  Priority-flag accuracy: 19/20 (95%)

| Reason | Correct |
|---|---|
| billing_error | 1/1 |
| duplicate | 5/5 |
| fraud | 8/9 |
| not_received | 4/4 |
| quality | 1/1 |

## Failures

- **E04** Fraud: abroad BUT card often used abroad: expected `escalate`, got `deny` (priority flag wrong)
