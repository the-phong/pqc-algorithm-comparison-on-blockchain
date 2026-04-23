# Availability Summary

| Mode | Success | Failure | Success Rate | Avg Latency (s) | P95 (s) | P99 (s) | Throughput (tx/s) | Retries | Avg Gas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| traditional | 5 | 0 | 100.0% | 11.250809 | 11.995968 | 12.023918 | 0.086140 | 0 | 248395.00 |
| pqc_hybrid | 3 | 2 | 60.0% | 22.841377 | 32.339473 | 33.090795 | 0.037738 | 4 | 268655.00 |
| pqc_confidential | 0 | 5 | 0.0% | - | - | - | 0.000000 | 10 | - |

## Source Files

- traditional: `availability_traditional.json`
- pqc_hybrid: `availability_pqc_hybrid.json`
- pqc_confidential: `availability_pqc_confidential.json`

## Error Breakdown

- traditional: none
- pqc_hybrid: insufficient_funds=2
- pqc_confidential: insufficient_funds=5
