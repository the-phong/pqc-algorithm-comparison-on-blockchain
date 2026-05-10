# Availability Summary

| Mode             |Success|Failure|Success Rate|Avg Latency(s)|  P95 (s)  |  P99 (s)  |Throughput (tx/s)| Retries |  Avg Gas  |
| ---------------- |-------|-------| ---------- | ------------ | --------- | --------- | --------------- |---------| --------- |
| traditional      |   5   |   0   |   100.0%   |  12.125454   | 13.223061 | 13.352819 |     0.079997    |    0    | 277813.20 |
| pqc_hybrid       |   5   |   0   |   100.0%   |  19.699095   | 37.324809 | 39.877639 |     0.049697    |    0    | 298135.60 |
| pqc_confidential |   5   |   0   |   100.0%   |  14.279073   | 22.370154 | 24.339692 |     0.068292    |    0    | 341157.20 |

## Source Files

- traditional: `availability_traditional.json`
- pqc_hybrid: `availability_pqc_hybrid.json`
- pqc_confidential: `availability_pqc_confidential.json`

## Error Breakdown

- traditional: none
- pqc_hybrid: none
- pqc_confidential: none
