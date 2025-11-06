import json

import pandas as pd
from rich.console import Console
from rich.table import Table

from config import STORE_DIR


class Visualizer:
    def __init__(self, yt_id: str) -> None:
        self.yt_id = yt_id
        self.root_store_dir = STORE_DIR
        self.response_dir = self.root_store_dir / yt_id / "responses"

    def clean_classified_response(self, reasoning=False):
        classified_response_pth = self.response_dir / "classified.csv"
        classified_df = pd.read_csv(classified_response_pth)
        headers = ["id", "timestamp", "class"]
        if reasoning:
            headers.append("reason")

        console = Console()
        rich_table = Table(
            show_header=True, header_style="bold magenta", show_lines=True
        )
        for column_name in headers:
            rich_table.add_column(column_name)

        for chunk in classified_df.iterrows():
            row = chunk[1]
            class_resp = str(row["class"])
            id = row["id"]
            timestamp = row["timestamp"]
            timestamp = timestamp[:8] + " - " + timestamp[13:21]

            start_index = class_resp.find("{")
            end_index = class_resp.rfind("}")
            if start_index != -1 and end_index != -1:
                json_string = class_resp[start_index : end_index + 1]
                # print(json_string)
                try:
                    class_resp_dict = json.loads(json_string)
                    cls = class_resp_dict["type"]
                    reason = class_resp_dict["reasoning"]
                    to_row = [
                        str(id),
                        str(timestamp),
                        str(cls),
                    ]
                    if reasoning:
                        to_row.append(str(reason))

                    if cls == "Irrelevant":
                        rich_table.add_row(
                            *to_row,
                            style="bold red",
                        )
                    elif cls == "Relevant":
                        rich_table.add_row(
                            *to_row,
                            style="bold green",
                        )

                    # table["reasoning"].append(class_resp_dict["reasoning"])
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    break
            else:
                print("No JSON found")
        console.print(rich_table)
