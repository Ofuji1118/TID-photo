# 学園祭フォトサービス 受け取り専用サイト

## 使い方

1. `index.html` を開く
2. 写真IDを入力する
3. `photo.html?id=写真ID` に移動する
4. `images/写真ID.jpg` が表示される
5. ダウンロードボタンから保存する

## 本番運用

撮影後、PC側でランダムIDを自動発行し、写真を次のように保存します。

```text
images/58392047.jpg
images/10483925.jpg
```

来場者には、共通QRコードと写真IDが書かれた紙を渡します。

共通QRコードに入れるURLは、GitHub Pagesなどで公開した `index.html` のURLです。

例：

```text
https://ユーザー名.github.io/gakusai-photo/
```

## テスト

`images/TEST1234.jpg` を入れてあります。

公開後、以下のようにアクセスして確認できます。

```text
https://ユーザー名.github.io/gakusai-photo/photo.html?id=TEST1234
```
