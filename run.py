import os
from edu_cut.preproc.pre_processor import PreProcessor
from edu_cut.ai.serve_ai import ServeAI 

gemma3 = {
    "base_url":"https://generativelanguage.googleapis.com/v1beta/openai/",
    "api_key":"GEMINI_API_KEY",
    "model":"gemma-3-4b-it",
}

x = PreProcessor("https://www.youtube.com/watch?v=O4bjWrhL4z0")
print(x.more_proc_merged())