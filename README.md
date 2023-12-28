# ez-chat-llm
Webブラウザから手軽にローカルLLMとおしゃべりできるソフトウェアです。([つくよみちゃんイラスト素材：花兎*様](https://tyc.rei-yumesaki.net/material/illust))
![eyecatch](eyecatch.png)

## はじめに
本リポジトリについては、[解説記事](https://zenn.dev/offtoung/articles/034d98bd397527)をあわせてご覧ください。

また、Google Colab Pro をお使いの方は、[こちらのノートブック](https://colab.research.google.com/drive/1LMLUNgGuV1ucEnqA1nDSKzMGs1SCMfus?usp=sharing)から、セットアップなしで手軽にお試しいただけます。

## セットアップ方法
### 下準備

**※2023/12/28現在、Windows と Cuda 12.3 の組み合わせでは PyTorch が GPU の認識に失敗するようです。Windows ユーザの方は、[WSL2](https://learn.microsoft.com/ja-jp/windows/wsl/install)などの Ubuntu 仮想環境をインストールし、その仮想環境の中で下記の作業をしていただくのがおすすめです。**

Anaconda 仮想環境の利用を推奨します。Anaconda は下記の URL からダウンロードできます。
https://www.anaconda.com/download

以下のコマンドは、本リポジトリ用に仮想環境 ezllm を作る方法の例です。
```
conda create -n ezllm python==3.8.5
conda activate ezllm
```

### 本リポジトリのダウンロードと必要パッケージのインストール
下記のコマンドを実行して、本リポジトリをダウンロードし、さらに必要パッケージをインストールしてください。
```
git clone https://github.com/offtoung/ez-chat-llm.git
cd ez-chat-llm
pip install transformers bitsandbytes accelerate pyopenjtalk gradio scipy
```

### ※インストールがうまくいかない場合
Ubuntu 22.04.3 LTS において動作確認が取れている依存パッケージのバージョンが本リポジトリの environment.yml に列挙されています。上記でうまくいかない場合は、
```
conda deactivate
conda remove -n ezllm --all
```
として、仮想環境を一旦削除し、
```
conda env create -f environment.yml 
```
をお試しください。

## 本ソフトウェアの起動方法
main.py を実行すると、gradioのサーバが起動します。
```
python main.py
```

### main.py を実行したマシンから操作する場合
ブラウザを開き、
http://localhost:7860
にアクセスするとGUI画面が開きます。

### 同じネットワーク内にある別のマシンから操作する場合
上記のURLの「localhost」をmain.pyを実行したマシンのホスト名またはIPアドレスに置き換えるとGUI画面にアクセスできます。

### 音声合成だけを行いたい場合
tts.py を実行すると、gradioのサーバが起動します。
```
python tts.py
```

## カスタムモデルの追加
### 対話モデルの追加方法
+ configs/llm にコンフィグ情報を記載した json ファイルを置いてください。json ファイルの書き方は、既存の json ファイルを参考にしてください。
+ 現在は、Hugging Face Transformers のモデルにのみ対応しています。
+ model_id には Hugging Face Model Hub のモデルIDか、モデルを格納したローカルディレクトリ名 (main.pyから見た相対パス) を設定できます。

### 音声合成モデルの追加方法
+ configs/voice にコンフィグ情報を記載した json ファイルを置いてください。json ファイルの書き方は、既存の json ファイルを参考にしてください。
+ 現在は、Hugging Face Transformers の VITS モデルにのみ対応しています。
+ model_id には Hugging Face Model Hub のモデルIDか、モデルを格納したローカルディレクトリ名 (main.pyから見た相対パス) を設定できます。

### 立ち絵の変更
+ figures ならびに figures/closed_eyes 内の画像を差し替えると立ち絵を変更できます。
+ 立ち絵 (感情) の種類自体を変更したい場合は、configs/emotion/emotion.json を編集してください。

## ライセンス
+ 本リポジトリのコード自体はMITライセンスで利用できます。
  - modules/ezllm/\_\_init\_\_.py には MITライセンスで配布されている ttslearn (https://github.com/r9y9/ttslearn) のコードを一部含みます。
  - 埋め込みモデルである [Multilingual-E5-large](https://huggingface.co/intfloat/multilingual-e5-large) を内部で利用しています。
+ 対話モデル、音声合成モデル、ならびに同梱している立ち絵のライセンスについては、下記を参照してください。
### 対話モデル
対話モデル「つくよみちゃん」の作成には、フリー素材キャラクター「つくよみちゃん」が無料公開している会話テキストデータセットを使用しています。

■つくよみちゃん会話AI育成計画 © Rei Yumesaki

https://tyc.rei-yumesaki.net/material/kaiwa-ai/

その他のモデルについては、Hugging Face Hub で公開されているものを参照しています。

|モデル名|URL1|URL2|ライセンス|
|:---|:---|:---|:---|
|つくよみちゃん(calm2-7b)|https://huggingface.co/offtoung/tsukuyomi-chan-calm2-7b|https://tyc.rei-yumesaki.net/material/kaiwa-ai|[つくよみちゃんキャラクターライセンス](https://tyc.rei-yumesaki.net/about/terms)＋[つくよみちゃん会話AI育成計画ライセンス (※1)](https://tyc.rei-yumesaki.net/material/kaiwa-ai)|
|calm2-7b-chat-GPTQ|https://huggingface.co/cyberagent/calm2-7b-chat|https://huggingface.co/TheBloke/calm2-7B-chat-GPTQ|Apache-2.0|
|calm2-7b-chat-GPTQ(美少女キャラ)|calm2-7b-chat-GPTQと同じ|calm2-7b-chat-GPTQと同じ|calm2-7b-chat-GPTQと同じ|
|ELYZA-japanese-Llama-2-7b-fast-instruct|https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-fast-instruct||LLAMA 2 Community License|
|youri-7b-chat-gptq|https://huggingface.co/rinna/youri-7b-chat-gptq||LLAMA 2 Community License|

(※1) 会話AIの動作画面等のスクリーンショット・キャプチャ動画の投稿、および会話AIから生成された会話を元ネタとする作品を公開する場合は、**「本ソフトウェアの名称 (ez-chat-llm) とつくよみちゃんの名前をクレジットすること」が必須**です。また、会話AIから生成された会話を素材として配布、会話AIから生成された会話を使用して新たな会話AIを作成、あるいは会話AIの改変・再配布を行う場合、[つくよみちゃん会話AI育成計画の利用規約](https://tyc.rei-yumesaki.net/material/kaiwa-ai)に従う必要があります。

### 音声モデル

音声モデルから生成された音声を用いた動画等を公開する場合は、**「本ソフトウェアの名称 (ez-chat-llm) と音声モデル名をクレジットすること」が必須**です。
|モデル名|URL1|URL2|ライセンス|
|:---|:---|:---|:---|
|つくよみちゃん|https://huggingface.co/offtoung/tsukuyomi-chan-vits|https://tyc.rei-yumesaki.net/material/corpus/|[つくよみちゃんキャラクターライセンス](https://tyc.rei-yumesaki.net/about/terms)＋[つくよみちゃんコーパスライセンス(※1)](https://tyc.rei-yumesaki.net/material/corpus/)|
|ルナイトネイル|https://huggingface.co/offtoung/runaitoneiru-vits|https://runaitoneiru.fanbox.cc/posts/3786422|[ルナイトネイルITAコーパス利用規約(※2)](https://runaitoneiru.fanbox.cc/posts/3786422)|
|黄琴海月(ひそひそ)|https://huggingface.co/offtoung/kikoto-kurage-hisohiso-vits|https://kikyohiroto1227.wixsite.com/kikoto-utau|[黄琴海月ITAコーパス利用規約(※3)](https://kikyohiroto1227.wixsite.com/kikoto-utau/ter%EF%BD%8Ds-of-service)

(※1)音声合成モデルの改変・再配布を行う場合は、[つくよみちゃんコーパスの利用規約](https://tyc.rei-yumesaki.net/material/corpus/)に従うことが必須です。

(※2)音声合成モデルの改変・再配布を行う場合は、[ルナイトネイルITAコーパス利用規約](https://runaitoneiru.fanbox.cc/posts/3786422)に従うことが必須です。

(※3)音声合成モデルの改変・再配布を行う場合は、[黄琴海月ITAコーパス利用規約](https://kikyohiroto1227.wixsite.com/kikoto-utau/ter%EF%BD%8Ds-of-service)に従うことが必須です。

### 立ち絵
同梱している立ち絵は、[花兎*様が制作された、つくよみちゃん万能立ち絵素材](https://tyc.rei-yumesaki.net/material/illust/)を改変したものです。この立ち絵はソフトウェアへ組み込んで公開することは許可されていますが、再配布は禁止されています。そのため、この立ち絵の改変や転用を行いたい方は、[元の配布場所](https://tyc.rei-yumesaki.net/material/illust/)から入手いただく必要があります。
詳しい利用規約については https://tyc.rei-yumesaki.net/material/illust/ をご参照ください。
