import json
import os

import pandas as pd
from rich.console import Console
from rich.table import Table

from config import STORE_DIR

# ==================== Helper Functions ====================


def _parse_timestamp(timestamp_str: str) -> tuple[float, float]:
    """Parse '00:01:34.000-00:01:38.500' to (start_seconds, end_seconds)."""
    parts = timestamp_str.split("-")
    start_parts = parts[0].split(":")
    end_parts = parts[1].split(":")

    start_secs = (
        float(start_parts[0]) * 3600
        + float(start_parts[1]) * 60
        + float(start_parts[2])
    )
    end_secs = (
        float(end_parts[0]) * 3600 + float(end_parts[1]) * 60 + float(end_parts[2])
    )
    return start_secs, end_secs


def _get_segment_duration(start: float, end: float) -> float:
    """Return duration in seconds."""
    return end - start


def _parse_classification(class_resp: str) -> str | None:
    """Extract 'type' from JSON response string."""
    start_index = class_resp.find("{")
    end_index = class_resp.rfind("}")
    if start_index != -1 and end_index != -1:
        try:
            json_obj = json.loads(class_resp[start_index : end_index + 1])
            return json_obj.get("type")
        except json.JSONDecodeError:
            return None
    return None


def _filter_irrelevant_segments(segments: list[dict]) -> list[dict]:
    """
    Apply filtering rules:
    - Rule 1: Irrelevant segment ≤1s with both neighbors NOT Irrelevant → exclude
    - Rule 2: Relevant segment ≤1s with both neighbors Irrelevant → treat as Irrelevant
    Returns list of segments that should be considered Irrelevant.
    """
    n = len(segments)
    filtered_classes = []

    for i, seg in enumerate(segments):
        cls = seg["classification"]
        duration = seg["duration"]

        prev_cls = segments[i - 1]["classification"] if i > 0 else None
        next_cls = segments[i + 1]["classification"] if i < n - 1 else None

        if cls == "Irrelevant":
            # Rule 1: Exclude short isolated irrelevant (< 2s and both neighbors NOT Irrelevant)
            if duration < 3.0 and prev_cls != "Irrelevant" and next_cls != "Irrelevant":
                filtered_classes.append("Relevant")  # Exclude from irrelevant
            else:
                filtered_classes.append("Irrelevant")
        # if cls == "Relevant":
        #     # Rule 2: Include short relevant between irrelevant (< 2s)
        #     if duration < 2.0 and prev_cls == "Irrelevant" and next_cls == "Irrelevant":
        #         filtered_classes.append("Irrelevant")  # Treat as irrelevant
        #     else:
        #         filtered_classes.append("Relevant")
        else:
            filtered_classes.append(cls)

    # Return only segments now classified as Irrelevant
    return [
        {**segments[i], "classification": filtered_classes[i]}
        for i in range(n)
        if filtered_classes[i] == "Irrelevant"
    ]


def _group_adjacent_segments(segments: list[dict]) -> list[dict]:
    """Group segments where segment[i].end == segment[i+1].start."""
    if not segments:
        return []

    groups = []
    current_group = {"start": segments[0]["start"], "end": segments[0]["end"]}

    for i in range(1, len(segments)):
        # Check if adjacent (end of current matches start of next)
        if abs(current_group["end"] - segments[i]["start"]) < 0.1:  # Small tolerance
            current_group["end"] = segments[i]["end"]
        else:
            groups.append(current_group)
            current_group = {"start": segments[i]["start"], "end": segments[i]["end"]}

    groups.append(current_group)
    return groups


def _format_time(seconds: float) -> str:
    """Convert seconds to 'Xm Ys' or 'Xh Ym Zs' format."""
    total_secs = round(seconds)  # Round to nearest second
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    secs = total_secs % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def _build_youtube_link(yt_id: str, seconds: float) -> str:
    """Build YouTube link with timestamp."""
    return f"https://www.youtube.com/watch?v={yt_id}&t={int(seconds)}s"


# ==================== Visualizer Class ====================


class Visualizer:
    def __init__(self, yt_id: str = None, direct_path: str = None) -> None:
        if yt_id and direct_path:
            raise ValueError("Provide either yt_id or direct_path, not both.")

        if yt_id:
            self.yt_id = yt_id
            self.root_store_dir = STORE_DIR
            self.response_path = (
                self.root_store_dir / yt_id / "responses/classified.csv"
            )
        elif direct_path:
            self.response_path = direct_path
            self.yt_id = os.path.basename(direct_path).split(".")[0]
        else:
            self.yt_id = None
            self.response_path = None

    def clean_classified_response(self, reasoning=False, exclude_groups: list[int] = None):
        """Display the raw unfiltered classification table.
        
        Args:
            reasoning: Whether to show reasoning column
            exclude_groups: List of group numbers (# column) to exclude from 2D list output
        """
        if exclude_groups is None:
            exclude_groups = []
        classified_df = pd.read_csv(self.response_path)
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
            raw_timestamp = row["timestamp"]

            # Extract start time for the link (00:00:00.000 -> seconds)
            try:
                start_part = raw_timestamp.split("-")[0].split(":")
                seconds = int(
                    float(start_part[0]) * 3600
                    + float(start_part[1]) * 60
                    + float(start_part[2])
                )
                link = f"https://www.youtube.com/watch?v={self.yt_id}&t={seconds}s"
            except (ValueError, IndexError):
                link = None

            timestamp_display = raw_timestamp[:8] + " - " + raw_timestamp[13:21]
            if link and self.yt_id:
                timestamp_display = f"[link={link}]{timestamp_display}[/link]"

            start_index = class_resp.find("{")
            end_index = class_resp.rfind("}")
            if start_index != -1 and end_index != -1:
                json_string = class_resp[start_index : end_index + 1]
                try:
                    class_resp_dict = json.loads(json_string)
                    cls = class_resp_dict["type"]
                    reason = class_resp_dict["reasoning"]
                    to_row = [
                        str(id),
                        timestamp_display,
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

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    print(json_string)
                    break
            else:
                print("No JSON found")

        console.print(rich_table)

        # Show grouped irrelevant segments below the main table
        self.show_grouped_irrelevant(console, exclude_groups=exclude_groups)

    def show_grouped_irrelevant(self, console: Console = None, exclude_groups: list[int] = None):
        """Display filtered and grouped irrelevant segments with clickable links.
        
        Args:
            console: Rich console for output
            exclude_groups: List of group numbers (# column) to exclude from 2D list output
        """
        if console is None:
            console = Console()
        
        if exclude_groups is None:
            exclude_groups = []

        classified_df = pd.read_csv(self.response_path)

        # Extract all segments with classification
        segments = []
        for _, row in classified_df.iterrows():
            raw_timestamp = row["timestamp"]
            class_resp = str(row["class"])

            try:
                start_secs, end_secs = _parse_timestamp(raw_timestamp)
            except (ValueError, IndexError):
                continue

            classification = _parse_classification(class_resp)
            if classification is None:
                continue

            segments.append(
                {
                    "id": row["id"],
                    "start": start_secs,
                    "end": end_secs,
                    "duration": _get_segment_duration(start_secs, end_secs),
                    "classification": classification,
                }
            )

        # Apply filtering rules
        irrelevant_segments = _filter_irrelevant_segments(segments)

        # Group adjacent segments (with segment tracking)
        grouped = self._group_adjacent_segments_with_ids(irrelevant_segments)

        # Filter out groups that are 3s or less
        # grouped = [g for g in grouped if (g["end"] - g["start"]) >= 2.0]

        # Count relevant segments (not in the grouped table)
        total_segments = len(segments)
        irrelevant_segment_count = len(irrelevant_segments)
        relevant_segment_count = total_segments - irrelevant_segment_count

        if not grouped:
            console.print(
                "\n[bold yellow]No irrelevant segments found after filtering.[/bold yellow]"
            )
            console.print(
                f"\n[bold green]Relevant segments (not shown): {relevant_segment_count}[/bold green]"
            )
            return

        # Build the table
        table = Table(
            title="[bold]Grouped Irrelevant Segments (Filtered)[/bold]",
            show_header=True,
            header_style="bold cyan",
            show_lines=True,
        )
        table.add_column("#", justify="right")
        table.add_column("Segments", justify="center")
        table.add_column("Count", justify="center")
        table.add_column("Start", justify="center")
        table.add_column("End", justify="center")
        table.add_column("Duration", justify="center")

        total_grouped_segments = 0
        for i, group in enumerate(grouped, 1):
            start_link = _build_youtube_link(self.yt_id, group["start"])
            start_display = f"[link={start_link}]{_format_time(group['start'])}[/link]"
            end_display = _format_time(group["end"])
            duration_display = _format_time(group["end"] - group["start"])
            
            # Format segment IDs that form this group
            segment_ids = group["segment_ids"]
            segment_count = len(segment_ids)
            total_grouped_segments += segment_count
            
            if segment_count <= 3:
                segments_display = ", ".join(str(sid) for sid in segment_ids)
            else:
                segments_display = f"{segment_ids[0]}-{segment_ids[-1]}"

            table.add_row(
                str(i),
                segments_display,
                str(segment_count),
                start_display,
                end_display,
                duration_display,
                style="bold red",
            )

        console.print("\n")
        console.print(table)
        
        # Show grouped segment total
        console.print(
            f"\n[bold red]Total grouped irrelevant segments: {total_grouped_segments}[/bold red]"
        )
        
        # Show relevant segment count summary
        console.print(
            f"[bold green]Relevant segments (not grouped/not shown above): {relevant_segment_count}[/bold green]"
        )
        
        # Print segment IDs as 2D list (excluding specified groups)
        segments_2d = [
            group["segment_ids"] 
            for i, group in enumerate(grouped, 1) 
            if i not in exclude_groups
        ]
        console.print(f"\n[bold cyan]Segments as 2D list:[/bold cyan] {segments_2d}")
        if exclude_groups:
            console.print(f"[dim](Excluded groups: {exclude_groups})[/dim]")

    def _group_adjacent_segments_with_ids(self, segments: list[dict]) -> list[dict]:
        """Group segments where segment[i].end == segment[i+1].start, tracking segment IDs."""
        if not segments:
            return []

        groups = []
        current_group = {
            "start": segments[0]["start"],
            "end": segments[0]["end"],
            "segment_ids": [segments[0]["id"]],
        }

        for i in range(1, len(segments)):
            # Check if adjacent (end of current matches start of next)
            if abs(current_group["end"] - segments[i]["start"]) < 0.1:  # Small tolerance
                current_group["end"] = segments[i]["end"]
                current_group["segment_ids"].append(segments[i]["id"])
            else:
                groups.append(current_group)
                current_group = {
                    "start": segments[i]["start"],
                    "end": segments[i]["end"],
                    "segment_ids": [segments[i]["id"]],
                }

        groups.append(current_group)
        return groups
