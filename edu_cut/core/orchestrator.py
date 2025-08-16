import json
from ..preproc.pre_processor import PreProcessor
from ..ai.serve_ai import ServeAI
import base64
from pathlib import Path


class Orchestrator:
    def __init__(self):
        self.pre_processor = PreProcessor("https://www.youtube.com/watch?v=Pi1-b50VHB8")
        self.llm = ServeAI()
        self.resp = self.pre_processor.yt_dir.joinpath("resp.jsonl")
        self.topic = self.pre_processor.yt_dir.joinpath("topic.txt")
        self.irr = self.pre_processor.yt_dir.joinpath("irr.jsonl")

    def get_summ(self):
        with open(
            "/home/znyd/hacking/edu-cut/store/Pi1-b50VHB8/merged_input.json",
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)
        prev_ctx = ""
        msg = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                    You are an advanced multimedia analyst AI, specializing in the critical evaluation of educational video content. Your primary function is to perform a deep, multi-modal analysis of a given video segment and produce a comprehensive description of it.

                    You will be provided with three key pieces of information for each segment:
                    1.  **`Context`**: Description of previous video segments description as context.
                    2.  **`Video Frames`**: A description or a series of images representing the visual content of the current segment.
                    3.  **`Transcript`**: The complete transcription of all spoken words in the current segment.

                    Your task is to synthesize this information by following a strict analytical process:

                    **Step 1: Visual Content Analysis**
                    First, meticulously analyze the provided `Video Frames`. Describe every visual element in detail **(Focus on the educational content)**. This includes:
                    *   Text, diagrams, slides, or any educational material visible on screen.
                    *   Any individuals present, their actions, and expressions.
                    *   Any objects or tools being used.
                    *   The environment.

                    **Step 2: Transcript Analysis**
                    Next, conduct a thorough analysis of the `Transcript`. Identify and summarize:
                    *   The primary topics and sub-topics of discussion.
                    *   Key concepts, definitions, and explanations provided by the speaker(s).
                    *   Any questions asked or answered.
                    *   The overall tone and nature of the dialogue.

                    **Step 3: Synthesized Multi-modal Description**
                    Finally, integrate your analyses from the previous steps into a single, detailed description of the video chunk.
                    This description must "spell out everything(focus on educational contents)" happening in the segment.
                    In your response, you must explicitly address the following:

                    Your final output should be a comprehensive narrative that provides a complete picture of the video segment but do not over explain anything
                    ,mentioning both the explicit educational content(main goal) and the contextual dynamics.
                    Just provide the description/explanation nothing else just the concise paragraph no follow up questions/suggestion or introductory message. 
                    Here is the context of previous video chunk:
                        """,
                    },
                ],
            }
        ]
        summ_msg = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """You are an Expert Educational Content Analyst specializing in synthesizing detailed multimedia evaluations into concise, contextful summaries.
                    You will be provided with a `Descriptive Analysis` educational video segments. This analysis is a comprehensive narrative detailing the 
                    segment's visual content, spoken transcript, and the relationship between them.
                    Your task is to read this detailed analysis and distill it into a summary that captures all of the essential findings.
                    ### **Your Goal**
                    Extract the core insights from the provided text. The summary should be brief,concise and 1 liner, focusing on the most critical 
                    information regarding the video segment's content and effectiveness.
                    ### **Output Format**
                    Your final output must be a clean, easily readable summary must in 1 line only not more than that. 
                                                """,
                    }
                ],
            }
        ]
        pth = Path("/home/znyd/hacking/edu-cut/store/Pi1-b50VHB8/frames")

        for idx, data_point in enumerate(data):
            chunk_msg = []
            if data_point["frames"]:
                for frame in data_point["frames"]:
                    print(frame)
                    chunk_msg.append(
                        {
                            "type": "text",
                            "text": "Here are the video frames of current video chunk:",
                        }
                    )
                    chunk_msg.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,"
                                + base64.b64encode(
                                    Path(pth.joinpath(frame)).read_bytes()
                                ).decode()
                            },
                        }
                    )

                chunk_msg.append(
                    {
                        "type": "text",
                        "text": f"""Here is the transcript/subtitle of this chunk: \n {data_point["transcript"]}""",
                    }
                )

                if idx == 0:
                    msg[0]["content"][0]["text"] += (
                        "It is the first video chunk so no previous context"
                    )
                else:
                    # compress_resp = self.llm.llm_response(
                    #     [
                    #         {
                    #             "role": "user",
                    #             "content": [
                    #                 {
                    #                     "type": "text",
                    #                     "text": f"""Just summarize all of the summary of these video chunks concisely retainning main points/informations: {ctx}""",
                    #                 }
                    #             ],
                    #         }
                    #     ]
                    # ).strip()
                    msg[0]["content"][0]["text"] += prev_ctx
                    prev_ctx = ""

                msg[0]["content"] += chunk_msg
                # clean_resp = re.sub(r'[\x00-\x1F\x7F\\\/]', '', clean_resp).replace("/", "").replace("\\", "").replace("‘", "'").replace("’", "'").replace("”", '"').replace("“", '"').replace("\n", "")

                try:
                    desc_resp = self.llm.llm_response(msg).strip()
                    print(desc_resp)
                    # summ_msg[0]["content"][0]["text"] += str(desc_resp)
                    # summ_resp = self.llm.llm_response(summ_msg).strip()
                    # print(summ_resp)
                    prev_ctx += desc_resp
                    resp_dict = {
                        "Description": str(desc_resp),
                        "id": idx,
                    }
                    print(resp_dict)

                    with open(self.resp, "a", encoding="utf-8") as f:
                        f.write(json.dumps(resp_dict, ensure_ascii=False) + "\n")

                except json.JSONDecodeError as e:
                    raise e

    def get_topic(self):
        data_load = []
        with open(self.resp, "r", encoding="utf-8") as f:
            for line in f:
                json_object = json.loads(line)
                data_load.append(json_object)

        msg = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """You are an AI assistant who can analyze description of chunks of an educational video and can tell about what is
                    this educational video is all about, basically the overall all the educational topics were taught on the video. Your response should be contains all the 
                    topics of this educational video. Don't include anything that is not related to academics or education. Here I am providing summary of every chunk of this whole video: """,
                    },
                ],
            }
        ]

        vid_desc = ""
        for data_point in data_load:
            vid_desc += data_point["Description"] + "\n"
        msg[0]["content"] += [{"type": "text", "text": vid_desc}]
        resp = self.llm.llm_response(msg)
        with open(self.topic, "w", encoding="utf-8") as f:
            f.write(resp)

    def get_irrelevant(self):
        with open(self.topic, "r") as f:
            topic = f.read()

        msg = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are an Expert AI Content Analyst. Your sole task is to determine if a specific chunk of an educational video is irrelevant(Main Goal) to the video's main topic
                        according to the given video chunk descriptions and transcription.
                        ### ## Criteria for Irrelevances
                        You must identify a chunk as irrelevant (`"is_irrelevant": "Yes"`) **only if** it meets one of the following conditions:s
                        1.  **Completely Off-Topic:** The content is entirely unrelated to the stated educational topic (e.g., the instructor discusses a movie, a personal story).
                        2.  **Non-Educational Distractions:** The chunk consists of significant dead air, technical troubleshooting (e.g., "Is my microphone working?"), or extended social chatter that does not contribute to the learning objective.
                        3.  **Mis-alignment:** Suppose the visual information is about something related to study/the video topic but speakers are talking about someting irrelevants

                        ### ## Relevant (What is NOT Irrelevant)
                        A chunk is **NOT** irrelevant (`"is_irrelevant": "No"`) if it contains:s
                        *   **Reflect the main video topics:** The visual information (texts, diagram etc) and the spoken information should align and must be relevant to the main video topic.

                        ### ## Instructions & Output Format

                        1.  Review the `Video Topic`, `Transcription` and `Chunk Description`(Remember mainly look for irrelevence if not then it would be relevant).
                        2.  Compare the description against the `Criteria for Irrelevance`(Mainly focus on detecting Irrelevat) and the `Relevance`.
                        3.  Provide your final answer exclusively in the following 2 line format, including a brief justification for your decision in the `reasoning` field.

                        "is_irrelevant": "Yes" | "No",
                        "reasoning": "A brief explanation of why the chunk is or is not irrelevant based on the provided criteria."
                        Here I am providing the overall topic of the whole educational video: {topic}
                        Here is the current chunk description (you will evaluate is this chunk irrelevant or not):""",
                    },
                ],
            }
        ]

        data_load = []
        with open(self.resp, "r", encoding="utf-8") as f:
            for line in f:
                json_object = json.loads(line)
                data_load.append(json_object)
        with open(
            "/home/znyd/hacking/edu-cut/store/Pi1-b50VHB8/merged_input.json",
            "r",
            encoding="utf-8",
        ) as f:
            trans = json.load(f)

        for data_point in data_load:
            msg[0]["content"] += [
                {
                    "type": "text",
                    "text": data_point["Description"]
                    + "\nHere is the transcription of this current chunk: "
                    + trans[data_point["id"]]["transcript"],
                }
            ]
            resp = str(self.llm.llm_response(msg))
            print(resp)

            with open(self.irr, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"id": data_point["id"], "irr": resp}, ensure_ascii=False
                    )
                    + "\n"
                )


o = Orchestrator()
# o.get_summ()
# o.get_topic()
o.get_irrelevant()

# get_summ->get_topic->get_irrelevant
