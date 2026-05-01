# BWSC DRL Optical Simulation Summary

- LED: CREE LED XHP70B-00-0000-0D0BN440E
- LED count: 6
- Drive current: 19.9 mA
- Source flux: 194.124 lm
- Exit flux: 154.523 lm
- Optical efficiency: 79.60 %
- I(0,0): 437.83 cd
- Imax: 461.01 cd
- Apparent surface: 6 x 25.00 x 25.00 mm = 37.50 cm2 (lens/front aperture: LEDiL C16369 HB-SQ-W 25x25 medium lens for XHP70.2; repeated one optic per LED)
- Apparent area: 37.50 cm2
- R148 category RL check: PASS

## R148 RL Measurement Points

| h [deg] | v [deg] | min [cd] | simulated [cd] | result |
|---:|---:|---:|---:|:---|
| -20 | -10 | 0 | 95.64 | PASS |
| -10 | -10 | 0 | 207.11 | PASS |
| -5 | -10 | 80 | 268.52 | PASS |
| 0 | -10 | 80 | 285.51 | PASS |
| 5 | -10 | 80 | 264.68 | PASS |
| 10 | -10 | 0 | 208.06 | PASS |
| 20 | -10 | 0 | 100.90 | PASS |
| -20 | -5 | 40 | 107.51 | PASS |
| -10 | -5 | 80 | 256.72 | PASS |
| -5 | -5 | 180 | 352.08 | PASS |
| 0 | -5 | 280 | 390.93 | PASS |
| 5 | -5 | 180 | 351.95 | PASS |
| 10 | -5 | 80 | 272.72 | PASS |
| 20 | -5 | 40 | 111.51 | PASS |
| -20 | 0 | 100 | 115.18 | PASS |
| -10 | 0 | 280 | 280.00 | PASS |
| -5 | 0 | 360 | 396.43 | PASS |
| 0 | 0 | 400 | 437.83 | PASS |
| 5 | 0 | 360 | 398.98 | PASS |
| 10 | 0 | 280 | 286.70 | PASS |
| 20 | 0 | 100 | 120.13 | PASS |
| -20 | 5 | 40 | 109.92 | PASS |
| -10 | 5 | 80 | 268.55 | PASS |
| -5 | 5 | 180 | 355.98 | PASS |
| 0 | 5 | 280 | 398.35 | PASS |
| 5 | 5 | 180 | 364.05 | PASS |
| 10 | 5 | 80 | 256.98 | PASS |
| 20 | 5 | 40 | 105.76 | PASS |
| -20 | 10 | 0 | 93.48 | PASS |
| -10 | 10 | 0 | 210.50 | PASS |
| -5 | 10 | 80 | 271.49 | PASS |
| 0 | 10 | 80 | 287.03 | PASS |
| 5 | 10 | 80 | 274.62 | PASS |
| 10 | 10 | 0 | 213.91 | PASS |
| 20 | 10 | 0 | 90.63 | PASS |

## Notes

- 設計検討用であり，最終的には実測フォトメトリが必要です。
- OpenGL表示の明るさは判定に使っていません。判定は数値計算された光度[cd]のみで行います。
- BWSC提出には実測フォトメトリ，色度測定，取付図，certifying engineer確認が必要です。
