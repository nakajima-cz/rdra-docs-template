# meta/ — テンプレート自体に関する資料（配布されない）

このディレクトリは **rdra-docs-template というリポジトリを保守するための資料置き場**。
`copier.yml` の `_subdirectory: template` により、copier が利用者のリポジトリへ展開するのは
`template/` 配下だけなので、ここに置いたファイルは**展開先には一切コピーされない**。

展開先に配りたいものは必ず `template/` 配下へ置くこと（逆に、配りたくない資料はここへ置く）。

## 収録物

- `diagrams/lifecycle-sequence.drawio` — 展開から運用・テンプレ更新追従までのライフサイクル（UMLシーケンス図）
- `diagrams/lifecycle-sequence.png` — 上記のレンダリング結果（閲覧・貼り付け用）
- `diagrams/lifecycle-sequence.spec.json` — 図の生成元 spec（図の正本はこちら。手で座標を触らない）

## 図の更新手順

1. `meta/diagrams/lifecycle-sequence.spec.json` を編集する（participants / steps / frames / legend）
2. 再生成する

```sh
python3 ~/.hermes/skills/creative/drawio-sequence-diagram/scripts/gen_sequence.py \
  meta/diagrams/lifecycle-sequence.spec.json meta/diagrams/lifecycle-sequence.drawio
```

3. PNG を出し直す（draw.io Desktop の CLI）

```sh
"/Applications/draw.io.app/Contents/MacOS/draw.io" -x -f png \
  -o meta/diagrams/lifecycle-sequence.png --scale 1.2 meta/diagrams/lifecycle-sequence.drawio
```

4. XML 妥当性を確認してからコミットする

```sh
python3 -c "import xml.dom.minidom as m; m.parse('meta/diagrams/lifecycle-sequence.drawio'); print('XML OK')"
```

注意: ラベルに `<...>` を書くと draw.io が HTML タグとして解釈して消える。`〈...〉`（全角山括弧）を使う。

## 除外の仕組み（配布範囲を変えたいとき）

- **既定の除外**: `_subdirectory: template` により `template/` 以外（`meta/`・ルート `README.md`・`copier.yml`）は配布対象外。
- **さらに個別除外したい場合**: `copier.yml` に `_exclude` を書く。パスは `_subdirectory` から見た相対で、
  既定値（`copier.y*ml` / `~*` / `__pycache__` / `.git` / `.DS_Store` など）を**上書き**するため、
  独自指定するときは既定値も書き戻すこと。

```yaml
_exclude:
  - "copier.yml"
  - "copier.yaml"
  - "~*"
  - "*.py[co]"
  - "__pycache__"
  - ".git"
  - ".DS_Store"
  - ".svn"
  - "配りたくないパス"
```
