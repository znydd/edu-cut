import base64
import json
import mimetypes
import re
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from config import PROMPT_DIR, STORE_DIR

from ..ai.serve_ai import ServeAI
from ..storage.store_manager import Storage


class Orchestrator:
    def __init__(self, yt_id: str, model: str):
        self.llm = ServeAI()
        self.storage = Storage()
        self.make_file = self.storage.make_file
        self.make_dir = self.storage.make_dir
        self.yt_id = yt_id
        self.model = model
        self.store_pth = STORE_DIR / yt_id
        self.prompt_dir = PROMPT_DIR
        self.merged_input = Path(f"{self.store_pth}/merged_input/merged_input.json")
        self.response_dir = self.store_pth / "responses"
        self.topic_pth = self.make_file(Path(f"{self.response_dir}/video_topic.txt"))
        # self.irr = self.make_file(Path(f"{self.store_pth}/irr.jsonl"))
        self.last_n_segment = 5

        self.resp = Path(f"{self.response_dir}/description.csv")
        if not self.storage.exist(self.resp):
            self.resp = self.make_file(Path(f"{self.response_dir}/description.csv"))
            pd.DataFrame(columns=pd.Index(["id", "timestamp", "description"])).to_csv(
                self.resp, index=False
            )

        self.desc_summ_pth = Path(f"{self.response_dir}/desc_summ.csv")
        if not self.storage.exist(self.desc_summ_pth):
            self.desc_summ_pth = self.make_file(
                Path(f"{self.response_dir}/desc_summ.csv")
            )
            pd.DataFrame(columns=pd.Index(["id", "timestamp", "summary"])).to_csv(
                self.desc_summ_pth, index=False
            )

        self.classified_pth = Path(f"{self.response_dir}/classified.csv")
        if not self.storage.exist(self.classified_pth):
            self.classified_pth = self.make_file(
                Path(f"{self.response_dir}/classified.csv")
            )
            pd.DataFrame(columns=pd.Index(["id", "timestamp", "class"])).to_csv(
                self.classified_pth, index=False
            )

    def video_topic_prompt(self, subtitle="", prompt_version="1") -> list:
        message = [{"role": "system", "content": ""}, {"role": "user", "content": None}]
        video_topic_sys_pth = f"{self.prompt_dir}/video_topic_sys_v{prompt_version}.txt"
        video_topic_pth = f"video_topic_v{prompt_version}.j2"
        env = Environment(loader=FileSystemLoader(self.prompt_dir))

        with open(video_topic_sys_pth, "r") as f:
            system_prompt = f.read()
        template = env.get_template(video_topic_pth)
        prompt = template.render(subtitle=subtitle)

        if subtitle and system_prompt and prompt:
            message[0]["content"] = system_prompt
            message[1]["content"] = prompt
        return message

    def video_description_prompt(
        self, prev_ctx: list, start: str, end: str, subtitle: str, frames: list
    ) -> list:
        with open(f"{self.prompt_dir}/video_description_sys.md", "r") as f:
            system_prompt = f.read()
        with open(self.topic_pth, "r") as f:
            video_topic = f.read()

        message = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": None},
        ]
        context_data = {
            "video_topic": video_topic,
            "chronological_context": prev_ctx,
            "start_time": start,
            "end_time": end,
            "transcript": subtitle,
        }

        env = Environment(loader=FileSystemLoader(self.prompt_dir))
        template = env.get_template("video_description.j2")
        prompt = template.render(context_data=context_data)
        message[1]["content"] = [{"type": "text", "text": prompt}]
        for frame in frames:
            message[1]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": self.image_to_base64_uri(
                            Path(f"{self.store_pth}/frames/{frame}")
                        )
                    },
                }
            )
        return message

    def video_classifier_prompt(
        self, curr_desc, start, end, prev_ctx, video_topic, subtitle
    ):
        with open(f"{self.prompt_dir}/final_prompt_vanila.md", "r") as f:
            class_sys_prompt = f.read()
        with open(self.topic_pth, "r") as f:
            video_topic = f.read()
        message = [
            {"role": "system", "content": class_sys_prompt},
            {"role": "user", "content": None},
        ]
        context_data = {
            "current_segment_description": curr_desc,
            "video_topic": video_topic,
            "chronological_context": prev_ctx,
            "start_time": start,
            "end_time": end,
            "transcript": subtitle,
        }
        env = Environment(loader=FileSystemLoader(self.prompt_dir))
        template = env.get_template("classification.j2")
        prompt = template.render(context_data=context_data)
        message[1]["content"] = [{"type": "text", "text": prompt}]

        return message

    def sec_to_hms(self, seconds) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02}:{minutes:02}:{secs:06.3f}"

    def image_to_base64_uri(self, filepath):
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type is None:
            raise ValueError(f"Could not determine MIME type for {filepath}")

        with open(filepath, "rb") as image_file:
            binary_data = image_file.read()
            base64_encoded_data = base64.b64encode(binary_data)
            base64_string = base64_encoded_data.decode("utf-8")

        return f"data:{mime_type};base64,{base64_string}"

    def get_video_topic(self, prompt_version="1"):
        subtitle_df = pd.read_csv(
            f"{self.store_pth}/subtitle/{self.yt_id}_transcript.csv"
        )
        subtitle = "\n ".join(subtitle_df["Segment"])
        prompt = self.video_topic_prompt(subtitle, prompt_version)
        response = self.llm.llm_response(prompt)

        with open(self.topic_pth, "w") as f:
            if response:
                response = re.sub(
                    r"<think>.*?</think>\s*", "", response, flags=re.DOTALL
                ).strip()
                f.write(response)
                print("Video topic generated and written to video_topic.txt✅")

    def get_video_description(self):
        with open(self.merged_input, "r", encoding="utf-8") as f:
            data = json.load(f)
        # prev_segments = pd.read_csv(self.desc_summ_pth)

        # Load existing descriptions to check for already processed segments
        existing_descriptions = pd.read_csv(self.resp)

        for idx, data_point in enumerate(data):
            # Skip if this segment already has a description
            if idx in existing_descriptions["id"].values:
                print(f"Skipping idx {idx} - description already exists")
                continue

            prev_segments = pd.read_csv(self.desc_summ_pth)
            if idx == 0:
                start, end = (
                    self.sec_to_hms(data_point["start"]),
                    self.sec_to_hms(data_point["end"]),
                )
                prev_ctx = [
                    {
                        "timestamp": "00:00:00-00:00:00",
                        "description": "The video starts from here and it is the first video chunk so no previous context",
                    }
                ]
            elif idx <= self.last_n_segment:
                start, end = (
                    self.sec_to_hms(data_point["start"]),
                    self.sec_to_hms(data_point["end"]),
                )
                prev_ctx = [
                    {
                        "timestamp": prev_segments[prev_segments["id"] == i].iloc[0][
                            "timestamp"
                        ],
                        "description": prev_segments[prev_segments["id"] == i].iloc[0][
                            "summary"
                        ],
                    }
                    for i in range(idx)
                ]
            else:
                start, end = (
                    self.sec_to_hms(data_point["start"]),
                    self.sec_to_hms(data_point["end"]),
                )
                prev_ctx = [
                    {
                        "timestamp": prev_segments[prev_segments["id"] == i].iloc[0][
                            "timestamp"
                        ],
                        "description": prev_segments[prev_segments["id"] == i].iloc[0][
                            "summary"
                        ],
                    }
                    for i in range(idx - self.last_n_segment, idx)
                ]

            # print(prev_ctx, idx)
            print(data_point["frames"])

            message = self.video_description_prompt(
                prev_ctx, start, end, data_point["transcript"], data_point["frames"]
            )

            description_response = self.llm.llm_response(message, self.model)

            if description_response:
                description_response = re.sub(
                    r"<think>.*?</think>\s*",
                    "",
                    description_response,
                    flags=re.DOTALL,
                ).strip()
                timestamp = start + "-" + end
                pd.DataFrame(
                    {
                        "id": [idx],
                        "timestamp": [timestamp],
                        "description": [description_response],
                    }
                ).to_csv(self.resp, mode="a", header=False, index=False)
                print(f"Description saved for {idx}->{start + end}")
                description_response += "\n Transcript: " + data_point["transcript"]
                self.get_description_summary(description_response, idx, timestamp)

    def get_description_summary(
        self, segment_description: str, idx: int, timestamp: str
    ):
        with open(Path(f"{self.prompt_dir}/segment_summary.md"), "r") as f:
            system_prompt = f.read()

        message = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": segment_description},
        ]
        summary_response = self.llm.llm_response(message, self.model)

        if summary_response:
            summary_response = re.sub(
                r"<think>.*?</think>\s*", "", summary_response, flags=re.DOTALL
            ).strip()

            pd.DataFrame(
                {"id": [idx], "timestamp": [timestamp], "summary": [summary_response]}
            ).to_csv(self.desc_summ_pth, mode="a", header=False, index=False)
            print(f"Summary saved for {idx}->{timestamp}")
            # print(summary_response)
            return summary_response
        return None

    def get_irrelevant(self):
        # 4 files to read: decription.csv, desc_summ.csv, merged.csv, video_topic.txt
        description_df = pd.read_csv(self.resp)
        # desc_summ_df = pd.read_csv(self.desc_summ_pth)
        prev_segments = pd.read_csv(self.desc_summ_pth)
        with open(self.merged_input, "r", encoding="utf-8") as f:
            subtitle_df = json.load(f)
        with open(self.topic_pth, "r") as f:
            video_topic = f.read()

        # Load existing classifications to check for already processed segments
        existing_classified = pd.read_csv(self.classified_pth)

        for idx, data_point in enumerate(subtitle_df):
            # Skip if this segment already has a classification
            if idx in existing_classified["id"].values:
                print(f"Skipping idx {idx} - classification already exists")
                continue
            start, end = (
                self.sec_to_hms(data_point["start"]),
                self.sec_to_hms(data_point["end"]),
            )
            if idx == 0:
                prev_ctx = [
                    {
                        "timestamp": "00:00:00-00:00:00",
                        "description": "The video starts from here and it is the first video chunk so no previous context",
                    }
                ]
            elif idx <= self.last_n_segment:
                prev_ctx = [
                    {
                        "timestamp": prev_segments[prev_segments["id"] == i].iloc[0][
                            "timestamp"
                        ],
                        "description": prev_segments[prev_segments["id"] == i].iloc[0][
                            "summary"
                        ],
                    }
                    for i in range(idx)
                ]
            else:
                prev_ctx = [
                    {
                        "timestamp": prev_segments[prev_segments["id"] == i].iloc[0][
                            "timestamp"
                        ],
                        "description": prev_segments[prev_segments["id"] == i].iloc[0][
                            "summary"
                        ],
                    }
                    for i in range(idx - self.last_n_segment, idx)
                ]
            curr_desc = description_df[description_df["id"] == idx].iloc[0][
                "description"
            ]

            message = self.video_classifier_prompt(
                curr_desc, start, end, prev_ctx, video_topic, data_point["transcript"]
            )
            classified_resp = self.llm.llm_response(message)
            # classified_resp= re.compile(r"<\|channel\|>final<\|message\|>(.*)", re.DOTALL).search(classified_resp).group(1).strip()
            save_format = {
                "id": [idx],
                "timestamp": [f"{start}-{end}"],
                "class": [f"{classified_resp}"],
            }
            pd.DataFrame(save_format).to_csv(
                self.classified_pth, mode="a", header=False, index=False
            )
            print(f"Classified saved for {idx}->{start + end}")
