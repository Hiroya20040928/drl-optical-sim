# BWSC DRL Optical Simulation Summary

- LED: CREE LED XHP70B-00-0000-0D0BN440E
- LED count: 1
- Drive current: 25.7 mA
- Source flux: 41.797 lm
- Exit flux: 33.437 lm
- Optical efficiency: 80.00 %
- I(0,0): 400.00 cd
- Imax: 400.00 cd
- Apparent surface: 60.00 x 45.00 mm (lens/front aperture: THEORETICAL target: CREE XHP70B R148 lower-bound 60x45 (not real lens))
- Apparent area: 27.00 cm2
- R148 category RL check: PASS

> WARNING: This run used the energy-consistent R148 lower-bound freeform target. It is NOT a real purchasable lens. It is a minimum-power design target, not a certified lamp or a substitute for measured photometry.

## R148 RL Measurement Points

| h [deg] | v [deg] | min [cd] | simulated [cd] | result |
|---:|---:|---:|---:|:---|
| -20 | -10 | 0 | 0.00 | PASS |
| -10 | -10 | 0 | 0.00 | PASS |
| -5 | -10 | 80 | 80.00 | PASS |
| 0 | -10 | 80 | 80.00 | PASS |
| 5 | -10 | 80 | 80.00 | PASS |
| 10 | -10 | 0 | 0.00 | PASS |
| 20 | -10 | 0 | 0.00 | PASS |
| -20 | -5 | 40 | 40.00 | PASS |
| -10 | -5 | 80 | 80.00 | PASS |
| -5 | -5 | 180 | 180.00 | PASS |
| 0 | -5 | 280 | 280.00 | PASS |
| 5 | -5 | 180 | 180.00 | PASS |
| 10 | -5 | 80 | 80.00 | PASS |
| 20 | -5 | 40 | 40.00 | PASS |
| -20 | 0 | 100 | 100.00 | PASS |
| -10 | 0 | 280 | 280.00 | PASS |
| -5 | 0 | 360 | 360.00 | PASS |
| 0 | 0 | 400 | 400.00 | PASS |
| 5 | 0 | 360 | 360.00 | PASS |
| 10 | 0 | 280 | 280.00 | PASS |
| 20 | 0 | 100 | 100.00 | PASS |
| -20 | 5 | 40 | 40.00 | PASS |
| -10 | 5 | 80 | 80.00 | PASS |
| -5 | 5 | 180 | 180.00 | PASS |
| 0 | 5 | 280 | 280.00 | PASS |
| 5 | 5 | 180 | 180.00 | PASS |
| 10 | 5 | 80 | 80.00 | PASS |
| 20 | 5 | 40 | 40.00 | PASS |
| -20 | 10 | 0 | 0.00 | PASS |
| -10 | 10 | 0 | 0.00 | PASS |
| -5 | 10 | 80 | 80.00 | PASS |
| 0 | 10 | 80 | 80.00 | PASS |
| 5 | 10 | 80 | 80.00 | PASS |
| 10 | 10 | 0 | 0.00 | PASS |
| 20 | 10 | 0 | 0.00 | PASS |

## Notes

- 設計検討用であり，最終的には実測フォトメトリが必要です。
- OpenGL表示の明るさは判定に使っていません。判定は数値計算された光度[cd]のみで行います。
- BWSC提出には実測フォトメトリ，色度測定，取付図，certifying engineer確認が必要です。
