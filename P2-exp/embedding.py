import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

class Embedding:
    def __init__(self):
        self.task = 'Given a search query on video description, retrieve relevant passages that answer the query'
     
    def average_pool(self, last_hidden_states: Tensor,
                     attention_mask: Tensor) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def get_detailed_instruct(self, task_description, query):
        return f'Instruct: {task_description}\nQuery: {query}'
    
    def load_model(self):
        tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large-instruct')
        model = AutoModel.from_pretrained('intfloat/multilingual-e5-large-instruct')
        return model, tokenizer

    def get_embeddings(self, txt, txt_type='docs'):
        if txt_type == "query":
            input_texts = self.get_detailed_instruct(self.task, txt)
        else:
            input_texts = txt

        model, tokenizer = self.load_model()

        # Tokenize the input texts
        batch_dict = tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors='pt')

        outputs = model(**batch_dict)
        embeddings = self.average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

        # normalize embeddings
        embeddings = F.normalize(embeddings, p=2, dim=1)

        # scores = (embeddings[:2] @ embeddings[2:].T) * 100
        # print(scores.tolist())

        return embeddings


