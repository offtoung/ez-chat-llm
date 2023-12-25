from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F
from torch import Tensor
import json
import numpy as np

class emotionManager():
  def __init__(self, conf_path):
    with open(conf_path, "r", encoding="utf-8") as f:
      self.emotions_dict = json.load(f)

    self.emotions = list(self.emotions_dict.keys())

    self.emotion_db = [f"passage: {x}" for x in self.emotions]
    self.emb_tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large')
    self.emb_model = AutoModel.from_pretrained('intfloat/multilingual-e5-large')

  def average_pool(self, last_hidden_states: Tensor,
                   attention_mask: Tensor) -> Tensor:
      last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
      return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

  def get_similarity(self, text):
    emotion_db=self.emotion_db
    tokenizer=self.emb_tokenizer
    model=self.emb_model

    input_texts = [f"query: {text}"]
    input_texts.extend(emotion_db)
    
    batch_dict = tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors='pt')

    outputs = model(**batch_dict)
    embeddings = self.average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    scores = (embeddings[:1] @ embeddings[1:].T) * 100
    scores = np.asarray(scores.tolist())

    argmax_idx = np.argmax(scores)
    return argmax_idx

  def get_emotion(self, text):
    argmax_idx = self.get_similarity(text)
    return self.emotions_dict[self.emotions[argmax_idx]]
