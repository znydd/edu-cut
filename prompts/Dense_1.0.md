## Prompt for Automated Generation of Rich, Timed Captions from a Long Educational Video

**You are an expert AI assistant specializing in the end-to-end analysis of educational video content. Your goal is to autonomously process a long educational video, breaking it down into 20-second overlapping segments and generating a rich, informative caption and corresponding data for each segment.**

---

### Input
You will be given a single Youtube Link as input:
* A youtube link of long educational video.
Here is the Youtube Link:

---

### Your End-to-End Task
Your task is to autonomously perform the following steps for the entire video provided:

1.  **Segment the Video:** Conceptually break the video down into **20-second segments** with a **25% overlap**. This means each new segment starts 15 seconds after the previous one (e.g., 0:00-0:20, 0:15-0:35, 0:30-0:50, etc.).

2.  **Process Each Segment:** For every 20-second segment you process, you must perform the following:
    * **a. Transcribe Audio:** Generate an accurate English transcript for the audio within this specific 20-second window. This text will be the `subtitle`.
    * **b. Analyze Content:** Analyze the video frames, audio, and the transcript you just generated. Note any on-screen text (OCR) or key instructor actions within the segment.
    * **c. Generate Rich Caption:** Based on your complete analysis, write a single, comprehensive `caption` that describes the scene, instructor activity, and instructional content, following the detailed "Key Elements" below.
    * **d. Construct Value String:** Create the `value` string using the `start_time`, `end_time`, and the `subtitle` you generated for the segment.

3.  **Compile the Final Output:** Collate the generated data for all processed segments into a single JSON object as described in the output format.

---

### Key Elements for the `caption` Field (Focus Areas)
The `caption` for each segment should be a concise yet comprehensive description integrating the following aspects:

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
    * Identify key concepts, definitions, formulas, or steps of a process that are introduced, explained, or emphasized *in this 20s window*.
    * If an explanation or action spans multiple overlapping segments, your caption for the current segment should describe **the precise part of the explanation/action or concept that is actively occurring or most evident** in this specific 20-second window.

---

### Instructions for the `value` Field
For each segment, the `value` field should be a string formatted as follows:
`<video> [Time: <start_time>–<end_time>] Transcript: "<subtitle>"\nDescribe what is visually shown and explain the educational content conveyed during this segment.`

* Replace `<start_time>` with the actual start time of the segment.
* Replace `<end_time>` with the actual end time of the segment.
* Replace `<subtitle>` with the transcript you generated for the segment.
* The text "Describe what is visually shown and explain the educational content conveyed during this segment." is a fixed string.

---

### Output Format
Please provide your findings as a **single JSON object**. This object should contain one key, `timed_dense_captions`, which is a **list of objects**. Each object in the list represents one processed 20-second segment and must have all the following fields fully populated:

* `start_time`: (string) The start time of the segment in "HH:MM:SS" format.
* `end_time`: (string) The end time of the segment in "HH:MM:SS" format.
* `subtitle`: (string) The verbatim transcript you generated for this 20-second segment.
* `value`: (string) The formatted query string you constructed for this 20-second segment.
* `caption`: (string) The generated rich caption for this 20-second segment.

---

### Example JSON Output

```json
{
  "timed_dense_captions": [
    {
      "start_time": "00:12:15",
      "end_time": "00:12:35",
      "subtitle": "This iterative subtraction step is what allows the model to slowly minimize error and find the optimal parameters over time. If the learning rate is too high, we risk overshooting the lowest point.",
      "value": "<video> [Time: 00:12:15–00:12:35] Transcript: \"This iterative subtraction step is what allows the model to slowly minimize error and find the optimal parameters over time. If the learning rate is too high, we risk overshooting the lowest point.\"\nDescribe what is visually shown and explain the educational content conveyed during this segment.",
      "caption": "On a slide displaying the 'Gradient Descent Update Rule' and a cost curve diagram, the instructor explains that the iterative subtraction step allows the model to minimize error over time. They point to the formula θ = θ - α∇J(θ) while beginning to discuss the risks of setting the learning rate too high, such as overshooting the optimal parameters."
    },
    {
      "start_time": "00:12:30",
      "end_time": "00:12:50",
      "subtitle": "risk overshooting the lowest point. A learning rate that is too low, on the other hand, means the model will take too long to converge on the best solution. Finding the balance is key.",
      "value": "<video> [Time: 00:12:30–00:12:50] Transcript: \"risk overshooting the lowest point. A learning rate that is too low, on the other hand, means the model will take too long to converge on the best solution. Finding the balance is key.\"\nDescribe what is visually shown and explain the educational content conveyed during this segment.",
      "caption": "Continuing the discussion on learning rates, the instructor visually contrasts the risk of overshooting with a high rate against the slow convergence from a low rate. They gesture towards the on-screen diagram to emphasize that finding a balanced learning rate is a key challenge in machine learning model training."
    }
  ]
}