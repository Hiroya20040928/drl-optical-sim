# CAD data status

Date: 2026-05-01

## Files

- `source/LEDiL_C16369_HB-SQ-W_datasheet.pdf`
  - Official LEDiL datasheet downloaded from:
    `https://www.ledil.com/data/prod/HighBay/16369/16369-ds.pdf`
- `source/LEDiL_C16369_HB-SQ-W_mechanical_drawing.pdf`
  - Official LEDiL mechanical drawing downloaded from:
    `https://www.ledil.com/data/prod/HighBay/16370/72bbdf-CA16370_HB-SQ-W%2020171023_MechanicalDrawing.pdf`
- `generated/CREE_XHP70B_00_0000_0D0BN440E_approx.step`
  - Approximate package model generated from public 7.00 mm x 7.00 mm x 4.35 mm package data.
- `generated/LEDiL_C16369_HB-SQ-W_approx.step`
  - Approximate lens envelope model generated from the LEDiL datasheet/mechanical drawing.
- `assembly/DRL_CREE_XHP70B_LEDiL_C16369_2x3_approx.step`
  - Approximate 2 x 3 DRL assembly with six LEDs and six lenses at 28 mm pitch.

## Official CAD availability

DigiKey lists an EDA/CAD model page for `XHP70B-00-0000-0D0BN440E`, and that page exposes a model entry named `XHP70.2.stp`. The underlying asset URL shown by DigiKey/Cree returned HTTP 404 when fetched on 2026-05-01, so the actual STEP file could not be downloaded non-interactively.

LEDiL's drawing states that LED fitting should be checked from a product-specific 3D model available from `www.ledil.com`, but the public product page exposes this as a request/download workflow rather than a direct STEP URL. The official 2D mechanical drawing and datasheet were downloaded and saved.

## Important limitation

The generated STEP files are dimensional layout models, not optical manufacturing models. The lens file preserves the public envelope dimensions relevant for packaging and apparent-surface discussions: 25 mm x 25 mm front aperture, 11.06 mm height, 25.4 mm adhesive tape outline, side bosses/notches, and the visible drawing geometry. It does not reproduce the proprietary internal aspheric/freeform optical surfaces exactly.

Use these files for packaging, placement, interference checks, and report figures. For mold tooling, ray-trace-grade CAD, or final compliance documentation, request official 3D data directly from LEDiL and Cree/DigiKey.

## Regeneration

The approximate STEP files were generated with:

```powershell
python -m pip install cadquery
python tools\generate_cad_models.py
```
