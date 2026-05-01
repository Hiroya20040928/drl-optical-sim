# BWSC DRL Optical Simulation Summary

- LED: CREE LED XHP70B-00-0000-0D0BN440E
- LED count: 4
- Drive current: 29.2 mA
- Source flux: 190.478 lm
- Exit flux: 151.610 lm
- Optical efficiency: 79.59 %
- I(0,0): 435.13 cd
- Imax: 468.14 cd
- Apparent surface: 4 x 25.00 x 25.00 mm = 25.00 cm2 (lens/front aperture: LEDiL C16369 HB-SQ-W 25x25 medium lens for XHP70.2; repeated one optic per LED)
- Apparent area: 25.00 cm2
- R148 category RL check: PASS

## R148 RL Measurement Points

| h [deg] | v [deg] | min [cd] | simulated [cd] | result |
|---:|---:|---:|---:|:---|
| -20 | -10 | 0 | 91.19 | PASS |
| -10 | -10 | 0 | 199.35 | PASS |
| -5 | -10 | 80 | 251.99 | PASS |
| 0 | -10 | 80 | 279.76 | PASS |
| 5 | -10 | 80 | 267.88 | PASS |
| 10 | -10 | 0 | 197.88 | PASS |
| 20 | -10 | 0 | 94.76 | PASS |
| -20 | -5 | 40 | 103.65 | PASS |
| -10 | -5 | 80 | 259.02 | PASS |
| -5 | -5 | 180 | 358.15 | PASS |
| 0 | -5 | 280 | 393.89 | PASS |
| 5 | -5 | 180 | 348.10 | PASS |
| 10 | -5 | 80 | 263.38 | PASS |
| 20 | -5 | 40 | 119.41 | PASS |
| -20 | 0 | 100 | 108.05 | PASS |
| -10 | 0 | 280 | 280.00 | PASS |
| -5 | 0 | 360 | 388.33 | PASS |
| 0 | 0 | 400 | 435.13 | PASS |
| 5 | 0 | 360 | 394.90 | PASS |
| 10 | 0 | 280 | 283.02 | PASS |
| 20 | 0 | 100 | 112.63 | PASS |
| -20 | 5 | 40 | 102.33 | PASS |
| -10 | 5 | 80 | 261.00 | PASS |
| -5 | 5 | 180 | 349.69 | PASS |
| 0 | 5 | 280 | 394.43 | PASS |
| 5 | 5 | 180 | 344.55 | PASS |
| 10 | 5 | 80 | 258.49 | PASS |
| 20 | 5 | 40 | 103.65 | PASS |
| -20 | 10 | 0 | 87.36 | PASS |
| -10 | 10 | 0 | 193.35 | PASS |
| -5 | 10 | 80 | 258.39 | PASS |
| 0 | 10 | 80 | 278.16 | PASS |
| 5 | 10 | 80 | 248.93 | PASS |
| 10 | 10 | 0 | 200.69 | PASS |
| 20 | 10 | 0 | 81.91 | PASS |

## Notes

- 設計検討用であり，最終的には実測フォトメトリが必要です。
- OpenGL表示の明るさは判定に使っていません。判定は数値計算された光度[cd]のみで行います。
- BWSC提出には実測フォトメトリ，色度測定，取付図，certifying engineer確認が必要です。
