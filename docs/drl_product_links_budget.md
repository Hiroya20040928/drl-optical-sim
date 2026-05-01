# CREE XHP70B + LEDiL C16369 DRL links and budget

Date: 2026-05-01

## Product links

### LED

- Part: CREE LED `XHP70B-00-0000-0D0BN440E`
- DigiKey: `https://www.digikey.com/en/products/detail/cree-led/XHP70B-00-0000-0D0BN440E/6802073`
- Datasheet: `https://downloads.cree-led.com/files/ds/x/XLamp-XHP70.2.pdf`
- DigiKey data checked on 2026-05-01:
  - 4000 K neutral white
  - 1710-1830 lm at test current
  - 2.1 A / 1.05 A, 6 V / 12 V
  - 125 deg viewing angle
  - 7.00 mm x 7.00 mm, 4.35 mm seated height
  - 1 pc price: USD 10.08
  - stock shown: 717

### Lens

- Part: LEDiL `C16369_HB-SQ-W`
- DigiKey Japan: `https://www.digikey.jp/ja/products/detail/ledil/C16369-HB-SQ-W/9095514`
- DigiKey accessible mirror used for price/spec check: `https://www.digikey.com.mx/es/products/detail/ledil/C16369-HB-SQ-W/9095514`
- LEDiL datasheet: `https://www.ledil.com/data/prod/HighBay/16369/16369-ds.pdf`
- LEDiL mechanical drawing: `https://www.ledil.com/data/prod/HighBay/16370/72bbdf-CA16370_HB-SQ-W%2020171023_MechanicalDrawing.pdf`
- DigiKey/LEDiL data checked on 2026-05-01:
  - 25 mm x 25 mm square lens
  - clear acrylic, adhesive mounting
  - one LED per optic
  - 53-65 deg viewing angle on DigiKey
  - LEDiL XHP70.2 optical table: FWHM 65 deg, efficiency 91 %
  - 1 pc price: USD 3.26
  - stock shown on accessible DigiKey page: 1882

## Apparent luminous surface explanation

The selected lens is 25 mm x 25 mm, but the 2 x 3 lamp layout has six independent lens fronts. The simulator therefore uses:

```text
apparent luminous area = 6 x 25 mm x 25 mm
                       = 3750 mm2
                       = 37.50 cm2
```

The `81 mm x 53 mm` value in the saved JSON is not the luminous area used for R148. It is the outer envelope of the array:

```text
array width  = 25 mm + 2 x 28 mm = 81 mm
array height = 25 mm + 1 x 28 mm = 53 mm
```

If the whole rectangle between the lenses were a glowing diffuser, the apparent area would be `81 x 53 / 100 = 42.93 cm2`. That is not the current design. The current design assumes six separate luminous lens fronts, so the R148 area check uses 37.50 cm2.

## Budget

Exchange rate used for the rough conversion:

- 1 JPY = USD 0.006360, so 1 USD = JPY 157.23
- Source checked on 2026-05-01: X-Rates

### Main 2 x 3 design, both left and right DRLs

The simulator's main recommendation is six LEDs and six lenses per DRL lamp, so the car uses 12 LEDs and 12 lenses total.

| Item | Qty | Unit price | Subtotal |
|---|---:|---:|---:|
| CREE `XHP70B-00-0000-0D0BN440E` | 12 | USD 10.08 | USD 120.96 |
| LEDiL `C16369_HB-SQ-W` | 12 | USD 3.26 | USD 39.12 |
| Active optical parts subtotal | - | - | USD 160.08 |
| Active optical parts subtotal | - | - | approx JPY 25,200 |

Add 10 % currency/procurement/tax cushion:

```text
USD 160.08 x 157.23 x 1.10 = approx JPY 27,700
```

Practical full pair budget, excluding photometry/certifying engineer fees:

```text
LEDs + lenses:                approx JPY 27,700
MCPCB / heat spreaders:        approx JPY 4,000 - 10,000
constant-current drivers:      approx JPY 3,000 - 8,000
connectors / wire / fuse:      approx JPY 2,000 - 5,000
housing / cover / sealant:     approx JPY 3,000 - 10,000
-------------------------------------------------------
rough pair total:              approx JPY 40,000 - 60,000
```

### 2 x 2 edge-pass design, both left and right DRLs

The edge-pass design uses four LEDs and four lenses per DRL lamp, so the car uses 8 LEDs and 8 lenses total.

| Item | Qty | Unit price | Subtotal |
|---|---:|---:|---:|
| CREE `XHP70B-00-0000-0D0BN440E` | 8 | USD 10.08 | USD 80.64 |
| LEDiL `C16369_HB-SQ-W` | 8 | USD 3.26 | USD 26.08 |
| Active optical parts subtotal | - | - | USD 106.72 |
| Active optical parts subtotal | - | - | approx JPY 16,800 |

This saves parts cost, but the apparent luminous surface is exactly 25.00 cm2, so there is no manufacturing margin against the R148 25 cm2 lower limit.
