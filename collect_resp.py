import shutil
from pathlib import Path

# --- CONFIGURATION ---
DESTINATION_DIR = (
    "/home/znyd/hacking/edu-cut/Benchmark/vanila_qwen3_4B_instruct_2507_indian_live"
)
# ---------------------


def collect_responses(dest_folder):
    # Ensure destination folder exists
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)

    store_path = Path("store")
    if not store_path.exists():
        print("Error: 'store' directory not found.")
        return

    count = 0
    # Iterate through each folder in 'store'
    for yt_folder in store_path.iterdir():
        if not yt_folder.is_dir():
            continue

        yt_id = yt_folder.name

        # Exact path specified by user: store/{yt_id}/responses/classified.csv
        csv_file = yt_folder / "responses" / "classified.csv"

        if csv_file.exists():
            try:
                target_name = f"{yt_id}.csv"
                target_path = dest_path / target_name

                print(f"Copying {csv_file} -> {target_path}")
                shutil.copy2(csv_file, target_path)
                count += 1
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")

    print(f"\nSuccessfully collected {count} files into '{dest_folder}'.")


if __name__ == "__main__":
    collect_responses(DESTINATION_DIR)
