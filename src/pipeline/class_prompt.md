### ROLE & GOAL ###
You are an intelligent retrieval expert. Your task is to analyze a user's query and find the most relevant sections within a structured list of video content summaries.

### CONTEXT & INPUT STRUCTURE ###
I am providing you with two pieces of information:
1.  **User Query:** The specific question the user is asking.
2.  **Video Content Index:** A JSON array where each object summarizes a 10-second clip from a video. Each object contains `chunk_timestamps`, a `summary_of_content`, and a list of `key_concepts_and_visuals`.

### PRIMARY OBJECTIVE ###
Your mission is to carefully read the User Query and then scan the entire Video Content Index. Identify all the `chunk_timestamps` that contain information relevant to answering the query.

Your final output must be a single, valid JSON object containing a list of the relevant timestamp strings. If no sections are relevant, return an empty list.

### REQUIRED JSON STRUCTURE ###
{
  "relevant_chunks": "array[string] | A list of the chunk_timestamps that directly address the user's query (e.g., ['10-20s', '30-40s'])."
}

---
---

### INPUT DATA ###

#### User Query ####
"On which section is the teacher teaching about MSE?"

#### Video Content Index ####
[
    {
        "chunk_timestamps": "0-10s",
        "summary_of_content": "The instructor introduces backpropagation as the core method for training neural networks by fine-tuning weights based on error rates.",
        "key_concepts_and_visuals": ["backpropagation definition", "neural network training", "fine-tuning weights", "error rate"]
    },
    {
        "chunk_timestamps": "10-20s",
        "summary_of_content": "The instructor explains different types of error calculation, including Mean Squared Error (MSE) and cross-entropy loss. The visual shows a formula for MSE.",
        "key_concepts_and_visuals": ["error calculation", "Mean Squared Error", "MSE", "cross-entropy loss", "MSE formula"]
    },
    {
        "chunk_timestamps": "20-30s",
        "summary_of_content": "The instructor details the process of calculating the gradient of a loss function with respect to the network's weights.",
        "key_concepts_and_visuals": ["gradient calculation", "loss function", "network weights", "calculus diagram"]
    }
]