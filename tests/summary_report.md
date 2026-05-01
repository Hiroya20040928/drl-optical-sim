# BWSC DRL Optical Simulation Summary

- LED: CREE LED XHP70B-00-0000-0D0BN440E
- LED count: 1
- Drive current: 20.3 mA
- Source flux: 33.060 lm
- Exit flux: 26.448 lm
- Optical efficiency: 80.00 %
- I(0,0): 702.40 cd
- Imax: 702.40 cd
- Apparent area: 27.00 cm2
- R148 category RL check: PASS

## R148 RL Measurement Points

| h [deg] | v [deg] | min [cd] | simulated [cd] | result |
|---:|---:|---:|---:|:---|
| -20 | -10 | 0 | 0.00 | PASS |
| -10 | -10 | 0 | 0.00 | PASS |
| -5 | -10 | 80 | 140.48 | PASS |
| 0 | -10 | 80 | 140.48 | PASS |
| 5 | -10 | 80 | 140.48 | PASS |
| 10 | -10 | 0 | 0.00 | PASS |
| 20 | -10 | 0 | 0.00 | PASS |
| -20 | -5 | 40 | 70.24 | PASS |
| -10 | -5 | 80 | 140.48 | PASS |
| -5 | -5 | 180 | 316.08 | PASS |
| 0 | -5 | 280 | 491.68 | PASS |
| 5 | -5 | 180 | 316.08 | PASS |
| 10 | -5 | 80 | 140.48 | PASS |
| 20 | -5 | 40 | 70.24 | PASS |
| -20 | 0 | 100 | 175.60 | PASS |
| -10 | 0 | 280 | 491.68 | PASS |
| -5 | 0 | 360 | 632.16 | PASS |
| 0 | 0 | 400 | 702.40 | PASS |
| 5 | 0 | 360 | 632.16 | PASS |
| 10 | 0 | 280 | 491.68 | PASS |
| 20 | 0 | 100 | 175.60 | PASS |
| -20 | 5 | 40 | 70.24 | PASS |
| -10 | 5 | 80 | 140.48 | PASS |
| -5 | 5 | 180 | 316.08 | PASS |
| 0 | 5 | 280 | 491.68 | PASS |
| 5 | 5 | 180 | 316.08 | PASS |
| 10 | 5 | 80 | 140.48 | PASS |
| 20 | 5 | 40 | 70.24 | PASS |
| -20 | 10 | 0 | 0.00 | PASS |
| -10 | 10 | 0 | 0.00 | PASS |
| -5 | 10 | 80 | 140.48 | PASS |
| 0 | 10 | 80 | 140.48 | PASS |
| 5 | 10 | 80 | 140.48 | PASS |
| 10 | 10 | 0 | 0.00 | PASS |
| 20 | 10 | 0 | 0.00 | PASS |

## Notes

- 設計検討用であり，最終的には実測フォトメトリが必要です。
- OpenGL表示の明るさは判定に使っていません。判定は数値計算された光度[cd]のみで行います。
- BWSC提出には実測フォトメトリ，色度測定，取付図，certifying engineer確認が必要です。
