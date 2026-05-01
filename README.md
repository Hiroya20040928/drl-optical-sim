# BWSC 2025 DRL Optical Simulator

BWSC 2025用DRL自作灯体の光学検討を行うための、Python/PySide6/OpenGLベースの簡易光線追跡・配光シミュレータです。

OpenGL表示は形状とrayの可視化用です。R148 category RL相当の合否判定は、Monte Carlo ray tracingで得た遠方配光の光度 `[cd]` だけを使います。

## 起動方法

Python 3.11以上を用意してください。

```powershell
cd E:\drl-optical-sim
python -m pip install -r requirements.txt
python main.py
```

GUIは常に表示されます。左側がOpenGL 3D表示、右上が入力パラメータ、右下がR148判定と配光ヒートマップです。

## 必要ライブラリ

- `PySide6`: GUI
- `PyOpenGL`: OpenGL 3D表示
- `numpy`: Monte Carlo ray tracingと配光集計
- `matplotlib`: 配光ヒートマップとPNG出力
- `pytest`: 単体テスト

## 主な機能

- LEDを点光源ではなく、矩形の小さな面光源としてrayを発生
- 指向特性を `I(theta)=I0*cos^n(theta)` で近似
- 指向角/FWHMから `n = log(0.5) / log(cos(theta_half))` を計算
- 電流変更時は初版として `flux = flux_nominal * current / current_nominal` で線形近似
- レンズなし、薄肉コリメーターレンズ、球面レンズ、平面拡散板、乳白アクリル拡散板
- Snellの法則、内部全反射、簡易Fresnel損失
- OBJ/STLメッシュ光学系へ拡張するための `MeshOptic` クラス
- 遠方球面上の水平角 `h[-30,+30] deg`、垂直角 `v[-20,+20] deg` 配光集計
- `dPhi / dOmega` による光度 `[cd]` 計算
- R148 category RL相当の測定点判定、最大光度1200 cd、見かけ面積25-200 cm2判定
- 見かけ面積は手入力値ではなく、選択した前面拡散板、レンズ開口、または裸LED外形から自動推定
- JSON/CSV/PNG/Markdown出力

## 出力ファイル

GUIの「結果保存」から以下を保存できます。

- `simulation_config.json`
- `intensity_map.csv`
- `r148_check.csv`
- `heatmap.png`
- `3d_view.png`
- `summary_report.md`

## LED仕様の追加方法

`data/leds.json` の `leds` 配列に項目を追加します。

必須に近い項目は以下です。

```json
{
  "id": "my_led",
  "name": "My LED",
  "flux_typ_lm": 100.0,
  "current_nominal_ma": 350.0,
  "current_default_ma": 250.0,
  "vf_typ_v": 3.3,
  "directivity_deg": 120.0,
  "package_mm": [8.0, 7.2, 6.0],
  "emitter_mm": [8.0, 7.2]
}
```

将来、電流-光束カーブを使う場合は `current_flux_curve` を追加できます。

```json
"current_flux_curve": [[50, 12.0], [100, 25.0], [350, 100.0]]
```

## レンズ仕様の追加方法

`data/lenses.json` の `lenses` 配列に追加します。初版で使える `kind` は以下です。

- `none`
- `thin_collimator`
- `spherical`
- `plane_diffuser`
- `milky_acrylic`
- `ideal_r148`

薄肉コリメーターレンズ例:

```json
{
  "id": "my_45deg_lens",
  "name": "My 45deg lens",
  "kind": "thin_collimator",
  "refractive_index": 1.49,
  "transmission": 0.9,
  "target_fwhm_deg": 45.0,
  "position_mm": 12.0
}
```

## R148 RL判定の意味

`data/r148_rl_table.csv` に内蔵した最小光度表を使い、各測定点のシミュレーション光度が最小値以上かを確認します。さらに以下も判定します。

- 全方向の最大光度 `Imax <= 1200 cd`
- 見かけ面積 `25 cm2 <= area <= 200 cm2`

画面とレポートには「設計検討用であり，最終的には実測フォトメトリが必要」と明記しています。このソフトは認証試験機ではありません。

## 実測が必要な理由

このシミュレータは初期設計の方向性を見るための簡易モデルです。実機では以下が配光に効きます。

- LED個体差、温度上昇、IF-Φ特性、Vfばらつき
- レンズや拡散板の実形状誤差、表面粗さ、材料ロット
- 筐体反射、遮光、取付角、前面カバーの透過率
- 色度、CCT、視認面積、測定器ジオメトリ

BWSC提出には、実測フォトメトリ、色度測定、取付図、certifying engineer確認が必要です。

## 本番LEDと実験用LEDの違い

本番想定LED `Nichia NF2W757H-V2H6 P12 5000K` は、65 mAで約37 lm、3.0 mm角パッケージ、Ra 90以上の小型高演色LEDです。1灯あたり2個直列、左右2灯の構成を想定しています。

実験用 `Akizuki OSW4XME1C1E-100` は、350 mA級で約100 lmのパワーLEDです。デフォルト電流は250 mAにしてあります。光束は大きい一方で、パッケージが大きく放熱要求も強いため、Nichia本番LEDとは発光面サイズ、熱設計、電流条件、色温度が異なります。

## CREE XHP70B最小電力ターゲット

`CREE LED XHP70B-00-0000-0D0BN440E` には、R148 RL最小配光をエネルギー整合させた理論下限ターゲット `CREE XHP70B R148 lower-bound freeform target 60x45` を追加しています。これは実商品レンズではなく、将来のfreeform/TIR/拡散前面設計が到達すべき最低電力側の目標です。

- default current: `25.664545 mA`
- electrical power estimate: `12.0 V * 25.664545 mA = 0.308 W`
- source flux: `41.797 lm`
- assumed optical efficiency: `80 %`
- exit flux: `33.438 lm`
- apparent surface: `60 mm x 45 mm = 27.0 cm2`

国内購入可能な実レンズ候補として、Carclo 10756、LEDiL F15539 JENNY-40、LEDiL C12868 FLARE-MAXIも登録しています。ただし公開cd/lmから見る限り、XHP70Bを25 mA級でR148 RLへ完全適合させる証拠にはなりません。実商品で通す場合は、完成灯体の実測配光が必要です。

## テスト

```powershell
cd E:\drl-optical-sim
python -m pytest -q
```

テスト内容:

- `cos^n` モデルの半値角が指定指向角になること
- 光学系なしで入力光束と遠方ビン合計が概ね一致すること
- R148表の読み込みと判定ロジック
- NF2W757H-V2H6 2個、65 mA、光学効率80%、R148最小配光1.756倍の理想モードで `I(0,0) ~= 702.5 cd`、`Imax < 1200 cd`
