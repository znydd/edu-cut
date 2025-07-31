# edu-cut

## In Progress

- Video Collection.
- Testing and making the pipeline for dataset creation.

## TODO

- [ ] Making English or Bengali Caption with Gemini 2.5 pro.
- [ ] Making a Dataset using Gemini 2.5 pro.
- [ ] A fine tuning of some VLM and testing the results.

## Done

- [x] InternVL2.5-1B image-videos test.
- [x] RAG test with llama-index and chromaDB.
- [X] Test with Embeddings on vector database.
- [X] Test educational video understanding.
- [X] Test Irreverent part capturing with gemini 2.5 pro

## Better video-text-to-text models

- [OpenGVLab](https://huggingface.co/OpenGVLab)

## Papers on embeddings

- [Text Embeddings by Weakly-Supervised Contrastive Pre-training](https://arxiv.org/pdf/2212.03533)
- [NV-EMBED: IMPROVED TECHNIQUES FOR TRAINING LLMS AS GENERALIST EMBEDDING MODELS](https://arxiv.org/pdf/2405.17428) [(ICLR2025)](https://iclr.cc/virtual/2025/poster/28505)
- [Jasper and Stella: distillation of SOTA embedding models-1.5B](https://arxiv.org/pdf/2412.19048)
- [A Comprehensive Survey of Sentence Representations:From the BERT Epoch to the CHATGPT Era and Beyond](https://aclanthology.org/2024.eacl-long.104.pdf)

## Goals

1. Remove Irreverent Segments from video.
2. Good at specific topic/course (Domain specific fine tuning -> catching errors + provide more context, example or different POV).
3. Video Search (RAG).
4. Long video handle.

## Branching
- master -> Production branch
- dev -> every feature will be developted on the dev branch then eventually be merged to master
- exp(Experimental) -> branch ideas will be tested here