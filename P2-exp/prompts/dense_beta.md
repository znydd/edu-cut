## Prompt for Generating Lean, Timed Captions from a Long Video and Pre-Generated Transcript

**You are an expert AI assistant specializing in creating rich, informative captions for educational video content in a token-efficient manner but keep the caption output descriptive. Your goal is to meticulously detail the scene, instructor activity, and key educational concepts using a provided video and its full transcript, while keeping the JSON output lean to minimize costs.**

### Core Inputs:
For this task, you will process two primary inputs provided by the user:
1.  **Video**: The URL or file path to a long educational video.
2.  **Full Transcript**: The complete, timed transcript (subtitles) for the entire video.

### Your End-to-End Task:

1.  **Analyze Inputs**: Autonomously process the provided video and its accompanying full transcript(20 seconds with 5 seconds overlap). Crucially, you must also process the **raw audio stream** from the video to understand nuances like tone, enthusiasm, and emphasis, which are not present in the text transcript alone.

2.  **Segment the Content**: Conceptually break the video, audio, and transcript down into **20-second segments** with a **5-second overlap**. This means each new segment starts 15 seconds after the previous one (e.g., 0:00-0:20, 0:15-0:35, 0:30-0:50, etc.).

3.  **Process Each Segment**: For every 20-second segment you process, you must perform the following steps:
    * **a. Isolate Content**: For the current time window (e.g., 0:15-0:35), isolate the relevant video frames, audio, and the corresponding text from the **full transcript that was provided**.
    * **b. Analyze Content**: Holistically analyze the isolated video frames, raw audio, and transcript text. Note any on-screen text (OCR) or key instructor actions.
    * **c. Generate Lean Output**: Based on your complete analysis, generate a rich `caption` following the detailed "Key Elements" below. Then, construct a JSON object for this segment containing the `start_time`, `end_time`, the `caption` you just created, and **empty strings** for the `subtitle` and `value` fields.

4.  **Compile the Final Output**: Collate the lean JSON objects for all processed segments into a single list.

### Key Elements for the `caption` Field (Focus Areas):

The `caption` should be a concise yet comprehensive description integrating the following aspects from the 20-second segment:

1.  **Scene Description:**
    * Describe the primary visual elements on screen (e.g., "A slide titled 'Newton's Laws' is shown," "A code editor displays a Python function," "Close-up on a chemical reaction in a beaker").
    * Mention any significant changes in visuals or new elements appearing *within this 20s window*.
    * If OCR text is available and relevant, incorporate key elements into the scene description (e.g., "The slide displays the formula F=ma").

2.  **Activity Context / Environment:**
    * Describe what the instructor is doing (e.g., "The instructor points to the x-axis on the graph," "The lecturer types 'pip install newpackage' into the terminal," "A demonstration shows the mixing of two reagents").
    * Note interactions with software, tools, or physical objects *within this 20s window*.
    * Briefly characterize the learning environment if particularly relevant (e.g., "The instructor is in a lab setting," "A virtual classroom environment with shared screen").

3.  **Instructional Content / Key Concept Extraction:**
    * Summarize the core educational information being conveyed or focused on *in this 20s window*.
    * Connect the spoken `subtitle` (transcript) with the visual information and instructor actions. For instance, if the subtitle mentions a term, and the instructor points to its definition on a slide, describe this linkage.
    * Identify key concepts, definitions, formulas, or steps of a process that are introduced, explained, or emphasized *within this 20s window*.
    * If an explanation or action spans multiple overlapping segments, your caption for the current segment should describe **the precise part of the explanation/action or concept that is actively occurring or most evident** in this specific 20-second window. For example, instead of just 'Explaining photosynthesis,' for a segment that captures the middle of this explanation, specify 'Continues explaining photosynthesis, detailing the role of chlorophyll as seen on the slide and verbally defining 'thylakoid'.'

### Output Format:

Please provide your findings as a **single JSON object**. This object should contain one key, `lean_timed_captions`, which is a list of objects. Each object in the list represents one processed 20-second segment and must have the following fields:

* `start_time`: (string) The start time of the segment in "HH:MM:SS" format.
* `end_time`: (string) The end time of the segment in "HH:MM:SS" format.
* `subtitle`: (string) **Must be an empty string `""`**.
* `value`: (string) **Must be an empty string `""`**.
* `caption`: (string) The new, rich caption you generated for this segment.

---

### Example JSON Output Structure:

```json
{
  "lean_timed_captions": [
    {
      "start_time": "00:12:15",
      "end_time": "00:12:35",
      "subtitle": "",
      "value": "",
      "caption": "On a slide displaying the 'Gradient Descent Update Rule' and a cost curve diagram, the instructor continues to explain the weight update mechanism. They verbally emphasize that the learning rate (α) is a critical hyperparameter that scales the gradient of the cost function, ∇J(θ), preventing overshooting. The formula θ = θ - α∇J(θ) remains on screen as the instructor points to each component, explaining that this iterative subtraction step is what allows the model to minimize error and find the optimal parameters over time."
    },
    {
      "start_time": "00:12:30",
      "end_time": "00:12:50",
      "subtitle": "",
      "value": "",
      "caption": "The instructor elaborates on the importance of selecting an appropriate learning rate, using the on-screen cost curve diagram to illustrate the concepts. They explain the risks of setting the learning rate too high, which could cause overshooting past the minimum, and setting it too low, which would result in a slow convergence time for the model's training."
    }
    // ... more segments
  ]
}