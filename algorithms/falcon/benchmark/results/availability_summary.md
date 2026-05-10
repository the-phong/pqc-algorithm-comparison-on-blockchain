# Availability Summary

| Mode             |Success|Failure|Success Rate|Avg Latency(s)|   P95(s)  |  P99(s)   |Throughput(tx/s)|Retries|Avg Gas|
| ---------------- |-------|-------|------------|--------------|-----------|-----------|----------------|-------|-------|
| traditional      |   5   |   0   |   100.0%   |   12.125454  | 13.223061 | 13.352819 |    0.079997    |   0   | 277813.20 |
| pqc_hybrid       |   5   |   0   |   100.0%   |   10.109404  | 12.740128 | 12.823178 |    0.095000    |   0   | 298147.60 |
| pqc_confidential |   5   |   0   |   100.0%   |   10.841261  | 11.671398 | 11.700767 |    0.088956    |   0   | 341169.20 |

## Source Files

- traditional: `availability_traditional.json`
- pqc_hybrid: `availability_pqc_hybrid.json`
- pqc_confidential: `availability_pqc_confidential.json`

## Error Breakdown

- traditional: none
- pqc_hybrid: none
- pqc_confidential: none
