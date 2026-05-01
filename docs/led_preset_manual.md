# LED preset manual

このマニュアルは、`drl-optical-sim` に新しいLEDプリセットを追加するための手順と、`data/leds.json` の書き方をまとめたものです。

## 追加するファイル

LEDプリセットは次のファイルに追加します。

```text
data/leds.json
```

ファイル全体はJSON形式で、最上位に `leds` 配列があります。新しいLEDは、この配列の末尾に1つのJSONオブジェクトとして追加します。

```json
{
  "leds": [
    {
      "id": "existing_led",
      "name": "Existing LED"
    },
    {
      "id": "new_led_id",
      "name": "New LED name"
    }
  ]
}
```

JSONなので、各項目の間にはカンマが必要です。ただし、配列やオブジェクトの最後の項目の後ろにはカンマを付けません。

## 最小構成

まず動かすだけなら、以下が最小構成です。

```json
{
  "id": "example_1w_white_led",
  "name": "Example 1W White LED",
  "manufacturer": "Example",
  "flux_typ_lm": 100.0,
  "current_nominal_ma": 350.0,
  "current_default_ma": 250.0,
  "vf_typ_v": 3.3,
  "directivity_deg": 120.0,
  "package_mm": [8.0, 8.0, 6.0],
  "emitter_mm": [6.0, 6.0],
  "default_leds_per_lamp": 1,
  "default_lamps": 1,
  "notes": "Example preset. Replace values with datasheet values."
}
```

この例では、350 mAで100 lmのLEDを、GUI初期値では250 mAで使います。電流変更時の光束は、初期実装では線形近似されます。

```text
flux_at_current = flux_typ_lm * current_ma / current_nominal_ma
```

つまり上の例で250 mAにすると:

```text
100 lm * 250 mA / 350 mA = 71.43 lm/LED
```

## 必須項目

### `id`

プログラム内部で使う一意のIDです。

推奨:

- 半角英数字とアンダースコアだけ
- 小文字
- メーカー名、型番、色温度、binなどを含める

例:

```json
"id": "nichia_nf2w757h_v2h6_p12_5000k"
```

悪い例:

```json
"id": "My LED"
```

スペースや日本語は避けてください。GUI表示名には `name` を使います。

### `name`

GUIに表示する名前です。人間が読める正式名称を書きます。

```json
"name": "Nichia NF2W757H-V2H6 P12 5000K"
```

### `flux_typ_lm`

1 LEDあたりの代表光束です。単位はlmです。

重要:

- `current_nominal_ma` で指定した電流における光束を書きます。
- 複数LED合計の光束ではありません。
- ランプ全体の光束でもありません。

例:

```json
"flux_typ_lm": 37.0,
"current_nominal_ma": 65.0
```

これは「65 mAで37 lm/LED」という意味です。

### `current_nominal_ma`

`flux_typ_lm` の測定条件または定格条件の電流です。単位はmAです。

例:

```json
"current_nominal_ma": 1050.0
```

CREE XHP70Bのように「1710 lm at 1050 mA」と読める場合は、`flux_typ_lm = 1710.0`、`current_nominal_ma = 1050.0` とします。

低電流で使う予定でも、`current_nominal_ma` にはデータシートの光束基準電流を入れてください。予定電流は `current_default_ma` に入れます。

### `current_default_ma`

GUIでそのLEDを選んだときの初期電流です。単位はmAです。

例:

```json
"current_default_ma": 20.3
```

### `vf_typ_v`

順方向電圧の代表値です。単位はVです。

消費電力表示や予算/設計検討で使います。

```text
power = vf_typ_v * current_ma * led_count / 1000
```

例:

```json
"vf_typ_v": 12.0
```

### `directivity_deg`

指向角または半値全角です。単位はdegreeです。

このソフトでは、仕様にある「directivity」「viewing angle」「half intensity angle」がfull width at half maximumとして与えられている前提で扱います。

内部では次の式でcosine-power指数に変換します。

```text
theta_half = directivity_deg / 2
n = log(0.5) / log(cos(theta_half))
I(theta) = I0 * cos(theta)^n
```

例:

```json
"directivity_deg": 120.0
```

### `package_mm`

LEDパッケージ外形寸法です。単位はmmで、順番は `[幅, 高さ, 厚み]` です。

```json
"package_mm": [7.0, 7.0, 4.34]
```

OpenGL表示、レンズなし時の見かけ面積推定、CAD/配置検討に使います。

### `emitter_mm`

発光面としてrayを出す矩形面の寸法です。単位はmmで、順番は `[幅, 高さ]` です。

```json
"emitter_mm": [7.0, 7.0]
```

発光面の詳細が不明な場合は、初期値としてパッケージ幅・高さと同じ値を入れて構いません。ただし、厳密には実発光部や蛍光体面の寸法を使うほど良いです。

## 任意項目

### `manufacturer`

メーカー名です。

```json
"manufacturer": "Cree LED"
```

### `store`

購入先や販売店名です。プログラムの計算には使いませんが、後から根拠を追うのに便利です。

```json
"store": "共立電子"
```

### `cct_k`

色温度です。単位はKです。不明なら `null` にします。

```json
"cct_k": 5000
```

```json
"cct_k": null
```

### `flux_min_lm`, `flux_max_lm`

光束binや範囲がある場合に書きます。単位はlmです。

```json
"flux_min_lm": 36.0,
"flux_max_lm": 42.8
```

現時点の標準計算では `flux_typ_lm` を使います。min/maxは資料・レポート用の根拠として保存されます。

### `vf_min_v`, `vf_max_v`

Vf範囲がある場合に書きます。

```json
"vf_min_v": 3.0,
"vf_max_v": 3.4
```

### `current_max_ma`

最大電流です。単位はmAです。

```json
"current_max_ma": 400.0
```

現時点では主に参照情報です。電流設定時の物理的な上限確認に使う値として保存しておきます。

### `board_mm`

アルミ基板付きLEDなど、LED基板の外形寸法です。単位はmmで、順番は `[幅, 高さ]` です。

```json
"board_mm": [21.13, 21.13]
```

現在の見かけ面積計算では、レンズなし時は `package_mm` を優先しています。基板全体が光るわけではないためです。基板寸法は実装・放熱・CAD検討用のメモとして使います。

### `cri_ra_min`, `r9_min`

演色性の情報です。

```json
"cri_ra_min": 90,
"r9_min": 50
```

DRL適合の光度計算には使いませんが、LED選定資料として残します。

### `default_leds_per_lamp`

GUIでそのLEDを選んだときの初期LED個数です。

```json
"default_leds_per_lamp": 2
```

### `default_lamps`

左右灯数など、設計前提の灯数メモです。

```json
"default_lamps": 2
```

現時点のシミュレーションは1灯ごとの配光を計算します。左右2灯合計を自動で足す値ではありません。

### `planned_operating_current_ma`

実験や設計で予定している運用電流です。計算には直接使いません。

```json
"planned_operating_current_ma": 20.3
```

GUI初期電流として使いたい場合は、同じ値を `current_default_ma` にも入れてください。

### `optimized_current_ma`, `planned_operating_power_w`, `optimized_power_w`

過去の検討結果や最適化結果をメモする項目です。計算には直接使いません。

```json
"optimized_current_ma": 19.866463,
"optimized_power_w": 1.430385
```

### `source`

データの出典を書きます。

```json
"source": "datasheet URL / distributor page / user measurement"
```

### `notes`

自由記述です。bin条件、温度条件、注意点、換算方法を書いてください。

```json
"notes": "Datasheet flux condition is TJ=85 C, IF=1050 mA. Simulator uses linear scaling unless current_flux_curve is provided."
```

## 電流-光束カーブを書く方法

LEDの低電流域では、光束が電流に完全比例しないことがあります。その場合は `current_flux_curve` を追加します。

```json
"current_flux_curve": [
  [20.0, 28.0],
  [50.0, 72.0],
  [100.0, 150.0],
  [350.0, 520.0],
  [1050.0, 1710.0]
]
```

各点は `[電流_mA, 光束_lm_per_LED]` です。

重要:

- 光束は1 LEDあたりです。
- 電流はmAです。
- 点は昇順で書くのが読みやすいです。プログラム側では並べ替えて補間します。
- このカーブがある場合、`flux_typ_lm * current / current_nominal_ma` ではなく、カーブの線形補間が使われます。

例:

```json
{
  "id": "example_curve_led",
  "name": "Example LED with current-flux curve",
  "manufacturer": "Example",
  "flux_typ_lm": 1710.0,
  "current_nominal_ma": 1050.0,
  "current_default_ma": 20.0,
  "vf_typ_v": 12.0,
  "directivity_deg": 125.0,
  "package_mm": [7.0, 7.0, 4.35],
  "emitter_mm": [7.0, 7.0],
  "current_flux_curve": [
    [10.0, 14.0],
    [20.0, 30.0],
    [50.0, 78.0],
    [100.0, 160.0],
    [1050.0, 1710.0]
  ],
  "notes": "Example only. Replace the curve with measured or datasheet relative luminous flux data."
}
```

## データシートから値を読むときの注意

### 光束の条件を必ず見る

同じLEDでも、光束は電流、温度、binで変わります。

よくある表記:

```text
Luminous Flux: 1710 lm @ IF=1050 mA, TJ=85 C
```

この場合:

```json
"flux_typ_lm": 1710.0,
"current_nominal_ma": 1050.0
```

低電流で使うからといって、`current_nominal_ma` を低電流値にしないでください。例えば20.3 mA運用予定なら:

```json
"current_nominal_ma": 1050.0,
"current_default_ma": 20.3
```

とします。こうすると初期実装では:

```text
1710 lm * 20.3 / 1050 = 33.07 lm/LED
```

として計算されます。

### lm/Wから逆算する場合

データシートに光束がなく、効率だけある場合は:

```text
flux_lm = efficacy_lm_per_w * vf_v * current_a
```

例:

```text
150 lm/W, Vf=3.0 V, IF=0.35 A
flux = 150 * 3.0 * 0.35 = 157.5 lm
```

この場合:

```json
"flux_typ_lm": 157.5,
"current_nominal_ma": 350.0,
"vf_typ_v": 3.0
```

とします。`notes` に逆算したことを書いてください。

### 指向角の読み方

`Viewing angle 120 deg`、`Directivity 120 deg`、`2θ1/2 = 120 deg` は、このソフトではFWHMとして扱います。

もしデータシートが半角だけを示している場合は、full widthに直してください。

例:

```text
半値半角 = 60 deg
directivity_deg = 120.0
```

### 複数LEDモジュールの場合

基板にLEDが複数載ったモジュールを1プリセットとして登録する場合は、原則として「シミュレータ上の1 LED単位」に合わせます。

推奨:

- LEDチップ1個を1プリセットにする
- GUI側の `LED個数` で個数を指定する

どうしてもモジュール全体を1プリセットにする場合は、`flux_typ_lm` と `current_nominal_ma` をモジュール全体の値にし、`package_mm` と `emitter_mm` もモジュール全体として扱います。ただし、rayは1つの矩形発光面から出るため、複数点光源・複数発光面としては表現されません。

## 追加後の確認方法

### JSONの構文確認

PowerShellで:

```powershell
cd E:\drl-optical-sim
python -m json.tool data\leds.json > $null
```

何も表示されなければ構文はOKです。

### テスト実行

```powershell
python -m pytest -q
```

### GUIで確認

```powershell
python main.py
```

GUIの `LED選択` に追加した `name` が表示されれば読み込み成功です。

## よくある失敗

### カンマ忘れ

JSONでは、項目の間にカンマが必要です。

悪い例:

```json
"flux_typ_lm": 100.0
"current_nominal_ma": 350.0
```

良い例:

```json
"flux_typ_lm": 100.0,
"current_nominal_ma": 350.0
```

### 最後の項目にカンマを付ける

悪い例:

```json
"notes": "example",
```

良い例:

```json
"notes": "example"
```

### 電流単位をAで書く

このソフトの電流はmAです。

悪い例:

```json
"current_nominal_ma": 0.35
```

良い例:

```json
"current_nominal_ma": 350.0
```

### 光束をランプ全体で書く

`flux_typ_lm` は1 LEDあたりです。6 LED合計で600 lmなら、1 LEDあたり100 lmとして書きます。

悪い例:

```json
"flux_typ_lm": 600.0,
"default_leds_per_lamp": 6
```

良い例:

```json
"flux_typ_lm": 100.0,
"default_leds_per_lamp": 6
```

### 発光面サイズをレンズサイズにする

`emitter_mm` はLEDの発光面です。レンズや前面カバーのサイズではありません。

レンズの前面サイズは `data/lenses.json` に書きます。

## 完整なテンプレート

以下をコピーして値を置き換えれば、新しいLEDプリセットを作れます。

```json
{
  "id": "manufacturer_part_bin_cct",
  "name": "Manufacturer Part Bin CCT",
  "manufacturer": "Manufacturer",
  "store": "Store or distributor",
  "cct_k": 5000,
  "flux_typ_lm": 100.0,
  "flux_min_lm": 90.0,
  "flux_max_lm": 110.0,
  "current_nominal_ma": 350.0,
  "current_default_ma": 100.0,
  "current_max_ma": 1000.0,
  "vf_typ_v": 3.1,
  "vf_min_v": 2.8,
  "vf_max_v": 3.4,
  "directivity_deg": 120.0,
  "package_mm": [3.5, 3.5, 0.8],
  "emitter_mm": [2.8, 2.8],
  "cri_ra_min": 80,
  "r9_min": null,
  "default_leds_per_lamp": 1,
  "default_lamps": 1,
  "source": "datasheet URL or measurement note",
  "notes": "State bin, temperature condition, and any conversion assumptions."
}
```

`null` は「値なし」という意味です。不要な任意項目は削除しても構いません。
