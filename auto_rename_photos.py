from pathlib import Path
import csv
import shutil
import secrets
import time
from datetime import datetime

# =========================================================
# 学園祭フォトサービス 自動リネームプログラム
# =========================================================

# サイト用フォルダの場所
# 例：デスクトップに gakusai-photo-site を置いた場合
BASE_DIR = Path(r"C:\Users\hirok\TID-photo\gakusai-photo-site")

# Z9からLAN転送される画像を受け取るフォルダ
INCOMING_DIR = BASE_DIR / "incoming"

# Webサイトで公開する画像フォルダ
IMAGES_DIR = BASE_DIR / "images"

# 元画像のバックアップ保存先
BACKUP_DIR = BASE_DIR / "backup_originals"

# 受付用メモを保存するフォルダ
SLIPS_DIR = BASE_DIR / "slips"

# 対応表CSV
CSV_PATH = BASE_DIR / "photo_mapping.csv"

# 最新IDを記録するファイル
LATEST_ID_PATH = BASE_DIR / "latest_id.txt"

# GitHub Pagesで公開するURL
# GitHub Pages公開後、自分のURLに変更する
SITE_URL = "https://ユーザー名.github.io/gakusai-photo/"

# ランダムIDの桁数
ID_DIGITS = 8

# 対象にする画像形式
TARGET_EXTENSIONS = {".jpg", ".jpeg"}


def ensure_folders():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    SLIPS_DIR.mkdir(parents=True, exist_ok=True)


def wait_until_file_is_complete(path: Path, checks: int = 3, interval: float = 1.0) -> bool:
    """
    LAN転送中の画像を途中で処理しないために、
    ファイルサイズが数回連続で変わらないことを確認する。
    """
    last_size = -1
    stable_count = 0

    for _ in range(30):
        if not path.exists():
            return False

        current_size = path.stat().st_size

        if current_size > 0 and current_size == last_size:
            stable_count += 1
            if stable_count >= checks:
                return True
        else:
            stable_count = 0

        last_size = current_size
        time.sleep(interval)

    return False


def load_used_ids() -> set:
    """
    既に使われているIDを読み込む。
    imagesフォルダ内のファイル名とCSVの内容を確認する。
    """
    used = set()

    for file in IMAGES_DIR.glob("*.jpg"):
        used.add(file.stem)

    if CSV_PATH.exists():
        with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "写真ID" in row and row["写真ID"]:
                    used.add(row["写真ID"])

    return used


def make_random_id(used_ids: set) -> str:
    while True:
        photo_id = str(secrets.randbelow(10 ** ID_DIGITS)).zfill(ID_DIGITS)
        if photo_id not in used_ids:
            return photo_id


def append_csv(row: dict):
    exists = CSV_PATH.exists()

    with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "処理日時",
            "元ファイル名",
            "写真ID",
            "公開用ファイル名",
            "受け取りURL",
            "バックアップファイル名"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not exists:
            writer.writeheader()

        writer.writerow(row)


def make_slip_text(photo_id: str, url: str):
    """
    受付で渡す紙に書く内容のメモを作る。
    共通QRコードは index.html のURLを使うため、ここでは写真IDを確認できるようにする。
    """
    text = f"""学園祭フォトサービス

写真ID：{photo_id}

受け取り方法：
1. 共通QRコードを読み込む
2. 写真IDを入力する
3. 写真をダウンロードする

直接URL：
{url}

注意：
写真IDやURLを第三者に共有しないでください。
SNSへ投稿する場合は、写っている人の許可を取ってください。
"""

    slip_path = SLIPS_DIR / f"{photo_id}.txt"
    slip_path.write_text(text, encoding="utf-8")


def process_image(path: Path, used_ids: set):
    if path.suffix.lower() not in TARGET_EXTENSIONS:
        return

    if not wait_until_file_is_complete(path):
        print(f"[スキップ] 転送完了を確認できませんでした: {path.name}")
        return

    photo_id = make_random_id(used_ids)
    used_ids.add(photo_id)

    public_filename = f"{photo_id}.jpg"
    public_path = IMAGES_DIR / public_filename

    # 公開用画像としてコピー
    shutil.copy2(path, public_path)

    # 元画像はバックアップに移動
    backup_filename = f"{photo_id}_{path.name}"
    backup_path = BACKUP_DIR / backup_filename
    shutil.move(str(path), str(backup_path))

    photo_url = f"{SITE_URL.rstrip('/')}/photo.html?id={photo_id}"

    append_csv({
        "処理日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "元ファイル名": path.name,
        "写真ID": photo_id,
        "公開用ファイル名": public_filename,
        "受け取りURL": photo_url,
        "バックアップファイル名": backup_filename
    })

    LATEST_ID_PATH.write_text(photo_id, encoding="utf-8")
    make_slip_text(photo_id, photo_url)

    print()
    print("=" * 46)
    print("写真IDを発行しました")
    print(f"写真ID：{photo_id}")
    print(f"公開用画像：images/{public_filename}")
    print(f"受け取りURL：{photo_url}")
    print("=" * 46)
    print()


def main():
    ensure_folders()
    used_ids = load_used_ids()

    print("学園祭フォトサービス 自動リネームを開始しました")
    print(f"監視フォルダ: {INCOMING_DIR}")
    print(f"公開画像フォルダ: {IMAGES_DIR}")
    print("終了する場合は Ctrl + C を押してください")
    print("-" * 46)

    processed_paths = set()

    try:
        while True:
            files = sorted(
                p for p in INCOMING_DIR.iterdir()
                if p.is_file()
                and p.suffix.lower() in TARGET_EXTENSIONS
                and p not in processed_paths
            )

            for file in files:
                processed_paths.add(file)
                process_image(file, used_ids)

            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("自動リネームを終了しました。")


if __name__ == "__main__":
    main()
