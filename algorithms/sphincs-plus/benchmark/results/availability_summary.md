# Availability Summary

| Mode             |Success|Failure|Success Rate|Avg Latency(s)|   P95(s)  |  P99(s)   |Throughput(tx/s)|Retries|Avg Gas|
| ---------------- |-------|-------|------------|--------------|-----------|-----------|----------------|-------|-------|
| traditional      |   5   |   0   |   100.0%   |   12.125454  | 13.223061 | 13.352819 |    0.079997    |   0   | 277813.20 |
| pqc_hybrid       |   5   |   0   |   100.0%   |   10.498408  | 12.365750 | 12.495329 |    0.091765    |   0   | 298313.20 |
| pqc_confidential |   5   |   0   |   100.0%   |   10.799911  | 12.157183 | 12.301167 |    0.088838    |   0   | 341337.20 |

## Source Files

- traditional: `availability_traditional.json`
- pqc_hybrid: `availability_pqc_hybrid.json`
- pqc_confidential: `availability_pqc_confidential.json`

## Error Breakdown

- traditional: none
- pqc_hybrid: none
- pqc_confidential: none
