## Prompt for Generating Rich, Timed Captions and Query Values for Educational Video Segments (10s Overlapping Windows)

**You are an expert AI assistant specializing in creating rich, informative captions and corresponding query values for educational video content. Your goal is to meticulously detail the scene, instructor activity, and key educational concepts within specific 10-second, overlapping time windows of a video. This will produce a structured dataset for enhanced learning, searchability, and downstream tasks.**

### Video Processing Instructions:
The video content is to be analyzed in **10-second segments**, with a **50% overlap** between consecutive segments. This means each segment is 10 seconds long, and a new segment starts every 5 seconds. For example:
* Segment 1: 00:00:00 - 00:00:10
* Segment 2: 00:00:05 - 00:00:15
* Segment 3: 00:00:10 - 00:00:20
* Segment 4: 00:00:15 - 00:00:25
* And so on.

### Input for Each 10-Second Segment:
For each individual 10-second segment you process (e.g., 00:00:05 - 00:00:15), you will receive:
1.  The **video content** specific to that 10-second window.
2.  The **start time** of the segment (e.g., "00:00:05").
3.  The **end time** of the segment (e.g., "00:00:15").
4.  An accurate **timed transcript** of the spoken audio strictly within that 10-second window (this will be the `subtitle`).
5.  (If available) **Text extracted via OCR** from any slides or on-screen displays visible *within that 10-second window*.
6.  (If available) A brief **description of significant on-screen actions** by the instructor (e.g., "instructor is writing on a digital whiteboard," "instructor is pointing to a diagram") that occur *within that 10-second window*.

### Your Task:
Based *only* on the inputs provided for each specific 10-second segment, generate a single JSON object containing a descriptive `caption` and a formatted `value` string, along with the provided `start_time`, `end_time`, and `subtitle`.

### Key Elements for the `caption` Field (Focus Areas):

The `caption` should be a concise yet comprehensive description integrating the following aspects from the 10-second segment:

1.  **Scene Description:**
    * Describe the primary visual elements on screen (e.g., "A slide titled 'Newton's Laws' is shown," "A code editor displays a Python function," "Close-up on a chemical reaction in a beaker").
    * Mention any significant changes in visuals or new elements appearing *within this 10s window*.
    * If OCR text is available and relevant, incorporate key elements into the scene description (e.g., "The slide displays the formula F=ma").

2.  **Activity Context / Environment:**
    * Describe what the instructor is doing (e.g., "The instructor points to the x-axis on the graph," "The lecturer types 'pip install newpackage' into the terminal," "A demonstration shows the mixing of two reagents").
    * Note interactions with software, tools, or physical objects *within this 10s window*.
    * Briefly characterize the learning environment if particularly relevant (e.g., "The instructor is in a lab setting," "A virtual classroom environment with shared screen").

3.  **Instructional Content / Key Concept Extraction:**
    * Summarize the core educational information being conveyed or focused on *in this 10s window*.
    * Connect the spoken `subtitle` (transcript) with the visual information and instructor actions. For instance, if the subtitle mentions a term, and the instructor points to its definition on a slide, describe this linkage.
    * Identify key concepts, definitions, formulas, or steps of a process that are introduced, explained, or emphasized *within this 10s window*.
    * If an explanation or action spans multiple overlapping segments, your caption for the current segment should describe **the precise part of the explanation/action or concept that is actively occurring or most evident** in this specific 10-second window. For example, instead of just 'Explaining photosynthesis,' for a segment that captures the middle of this explanation, specify 'Continues explaining photosynthesis, detailing the role of chlorophyll as seen on the slide and verbally defining 'thylakoid'.'

### Instructions for the `value` Field:

The `value` field should be a string formatted as follows:
`<video> [Time: <start_time>–<end_time>] Transcript: "<subtitle>"\nDescribe what is visually shown and explain the educational content conveyed during this segment.`

* Replace `<start_time>` with the actual start time of the segment.
* Replace `<end_time>` with the actual end time of the segment.
* Replace `<subtitle>` with the actual transcript provided for the segment.
* The text "Describe what is visually shown and explain the educational content conveyed during this segment." is a fixed string.

### Style and Tone of the `caption`:

* **Rich and Informative:** Provide a comprehensive overview of the segment's educational content and context.
* **Objective and Factual:** Describe what is being taught, shown, and done.
* **Clear and Direct:** Use precise language.
* **Focus on Educational Value:** Prioritize information and actions that contribute to learning within that specific moment.
* **Third-Person Perspective.**

### What to AVOID:
* Summarizing content from outside the current 10s window.
* Generic descriptions like "teacher talks" or "slide shown." Be specific about *what* is said or *what* is on the slide.
* Including filler words from the `subtitle` unless they are crucial for context.
* Making assumptions beyond the provided information for the segment.

### Output Format (per 10-second segment):
Please provide your output as a **single JSON object** for each processed 10-second segment. This object must have the following fields:

* `start_time`: (string) The start time of the segment in "HH:MM:SS" format (e.g., "00:00:05").
* `end_time`: (string) The end time of the segment in "HH:MM:SS" format (e.g., "00:00:15").
* `subtitle`: (string) The verbatim transcript for this 10-second segment.
* `value`: (string) The formatted query string as described above.
* `caption`: (string) The generated rich caption for this 10-second segment, focusing on scene description, activity context, and instructional content.

---

### Example JSON Output for one 10-second segment:

(This example represents *one* such segment. The `start_time` and `end_time` would change for consecutive overlapping segments, e.g., "00:12:00"-"00:12:10", then "00:12:05"-"00:12:15", etc.)

```json
{
  "start_time": "00:12:05",
  "end_time": "00:12:15",
  "subtitle": "Now you see, gradient descent updates the weights by subtracting the learning rate multiplied by the gradient of the cost function. This step is crucial for minimizing error.",
  "value": "<video> [Time: 00:12:05–00:12:15] Transcript: \"Now you see, gradient descent updates the weights by subtracting the learning rate multiplied by the gradient of the cost function. This step is crucial for minimizing error.\"\nDescribe what is visually shown and explain the educational content conveyed during this segment.",
  "caption": "The instructor continues explaining the gradient descent update rule, shown on a slide with a cost curve diagram. They emphasize that weights are updated by subtracting the learning rate (α) times the cost function's gradient (∇J(θ)), reiterating the formula θ = θ - α∇J(θ). The importance of this step for error minimization is highlighted."
}