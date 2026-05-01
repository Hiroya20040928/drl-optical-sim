# BWSC DRL Optical Simulation Summary

- LED: CREE LED XHP70B-00-0000-0D0BN440E
- LED count: 1
- Drive current: 20.3 mA
- Source flux: 33.060 lm
- Exit flux: 33.060 lm
- Optical efficiency: 100.00 %
- I(0,0): 9.23 cd
- Imax: 18.78 cd
- Apparent area: 27.00 cm2
- R148 category RL check: FAIL

## R148 RL Measurement Points

| h [deg] | v [deg] | min [cd] | simulated [cd] | result |
|---:|---:|---:|---:|:---|
| -20 | -10 | 0 | 8.13 | PASS |
| -10 | -10 | 0 | 8.68 | PASS |
| -5 | -10 | 80 | 10.88 | FAIL |
| 0 | -10 | 80 | 11.16 | FAIL |
| 5 | -10 | 80 | 10.61 | FAIL |
| 10 | -10 | 0 | 7.99 | PASS |
| 20 | -10 | 0 | 8.82 | PASS |
| -20 | -5 | 40 | 8.44 | FAIL |
| -10 | -5 | 80 | 10.21 | FAIL |
| -5 | -5 | 180 | 9.80 | FAIL |
| 0 | -5 | 280 | 9.81 | FAIL |
| 5 | -5 | 180 | 10.21 | FAIL |
| 10 | -5 | 80 | 9.53 | FAIL |
| 20 | -5 | 40 | 10.08 | FAIL |
| -20 | 0 | 100 | 9.77 | FAIL |
| -10 | 0 | 280 | 9.63 | FAIL |
| -5 | 0 | 360 | 9.90 | FAIL |
| 0 | 0 | 400 | 9.23 | FAIL |
| 5 | 0 | 360 | 9.23 | FAIL |
| 10 | 0 | 280 | 8.68 | FAIL |
| 20 | 0 | 100 | 11.94 | FAIL |
| -20 | 5 | 40 | 9.94 | FAIL |
| -10 | 5 | 80 | 9.80 | FAIL |
| -5 | 5 | 180 | 11.71 | FAIL |
| 0 | 5 | 280 | 11.30 | FAIL |
| 5 | 5 | 180 | 9.26 | FAIL |
| 10 | 5 | 80 | 10.35 | FAIL |
| 20 | 5 | 40 | 9.53 | FAIL |
| -20 | 10 | 0 | 11.16 | PASS |
| -10 | 10 | 0 | 9.51 | PASS |
| -5 | 10 | 80 | 8.82 | FAIL |
| 0 | 10 | 80 | 10.47 | FAIL |
| 5 | 10 | 80 | 9.65 | FAIL |
| 10 | 10 | 0 | 8.68 | PASS |
| 20 | 10 | 0 | 11.16 | PASS |

## Notes

- 設計検討用であり，最終的には実測フォトメトリが必要です。
- OpenGL表示の明るさは判定に使っていません。判定は数値計算された光度[cd]のみで行います。
- BWSC提出には実測フォトメトリ，色度測定，取付図，certifying engineer確認が必要です。
