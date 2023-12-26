import re
from transformers import VitsTokenizer, VitsModel, VitsConfig
from typing import Any, Dict, List, Optional, Tuple
import pyopenjtalk
import torch
import numpy as np
import json

'''
Includes codes taken from ttslearn (https://github.com/r9y9/ttslearn) released under MIT Licence, Copyright (c) 2021 Ryuichi Yamamoto.
'''

def numeric_feature_by_regex(regex, s):
  match = re.search(regex, s)
  if match is None:
    return -50
  return int(match.group(1))

def pp_symbols(labels, drop_unvoiced_vowels=True):
  PP = []
  N = len(labels)

  for n in range(N):
    lab_curr = labels[n]
    p3 = re.search(r"\-(.*?)\+", lab_curr).group(1)

    if drop_unvoiced_vowels and p3 in "AEIOU":
      p3 = p3.lower()

    if p3 == "sil":
      assert n == 0 or n == N - 1
      if n == 0:
        PP.append("^")
      elif n == N - 1:
        e3 = numeric_feature_by_regex(r"!(\d+)_", lab_curr)
        if e3 == 0:
          PP.append("$")
        elif e3 == 1:
          PP.append("?")
      continue
    elif p3 == "pau":
      PP.append("_")
      continue
    else:
      PP.append(p3)

    a1 = numeric_feature_by_regex(r"/A:([0-9\-]+)\+", lab_curr)
    a2 = numeric_feature_by_regex(r"\+(\d+)\+", lab_curr)
    a3 = numeric_feature_by_regex(r"\+(\d+)/", lab_curr)
    f1 = numeric_feature_by_regex(r"/F:(\d+)_", lab_curr)

    a2_next = numeric_feature_by_regex(r"\+(\d+)\+", labels[n + 1])

    if a3 == 1 and a2_next == 1 and p3 in "aeiouAEIOUNcl":
      PP.append("#")
    elif a1 == 0 and a2_next == a2 + 1 and a2 != f1:
      PP.append("]")
    elif a2 == 1 and a2_next == 2:
      PP.append("[")

  return PP

class ezVitsTokenizer(VitsTokenizer):
  # Do nothing
  def prepare_for_tokenization(
    self, text: str, is_split_into_words: bool = False, normalize: Optional[bool] = None, **kwargs
  ) -> Tuple[str, Dict[str, Any]]:
    return text, kwargs

  def _tokenize(self, text: str) -> List[str]:
    text = text.strip("「（｛【『［＜《〈([{<")

    text = re.sub("？", "?", text)
    text = re.sub("\?\?+", "??", text)
    text = re.sub("！", "!", text)
    text = re.sub("\!\!+", "!!", text)
    text = re.sub("…", "_", text)

    pp = []
    subtexts = re.split('(\?|\!|_)', text)

    for st in subtexts:
      if st in ['?', '!', '_']:
        if len(pp) > 0: 
          if pp[-1] == '$':
            pp[-1] = st
          else: 
            pp.append(st)
      else:
        contexts = pyopenjtalk.extract_fullcontext(st)
        pp.extend(pp_symbols(contexts, drop_unvoiced_vowels=False))

    result = [0] * (len(pp) * 2 + 1)
    result[1::2] = pp

    return result

class ezttsConfig():
  def __init__(self, config_dict):
    if type(config_dict) is str:
      with open(config_dict, "r", encoding="utf-8") as f:
        config_dict = json.load(f)

    assert type(config_dict) == dict, "config_dict should be either a dictionary or a path to a json file"

    self.model_id = config_dict["model_id"]

    try:
      self.speaker_id = config_dict["speaker_id"]
    except:
      self.speaker_id = None

    try:
      self.model_name = config_dict["model_name"]
    except:
      self.model_name = self.model_id


class ezttsModel():
  def __init__(self, config_dict):
    self.config = ezttsConfig(config_dict)

    self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
    self.tokenizer = ezVitsTokenizer.from_pretrained(self.config.model_id)
    self.model = VitsModel.from_pretrained(self.config.model_id).to(self.device)
    self.sampling_rate = self.model.config.sampling_rate
    self.speaker_id = self.config.speaker_id

  def tts(self, text, speaker_id=0):
    text = re.sub("？", "?", text)
    text = re.sub("！", "!", text)
    text = text.strip()
    buff = re.split('(\n|\!|。|\?)', text)

    if len(buff) == 0:
      return None

    subtexts = []
    for idx, subtext in enumerate(buff):
      if subtext in ["\n", "!", "。", "?"] and idx >= 1:
        subtexts[-1] = subtexts[-1] + subtext
      else:
        subtexts.append(subtext)
         
    if(subtexts[-1] == ''):
      subtexts = subtexts[:-1]

    wav = np.array([])    
    for subtext in subtexts:
      inputs = self.tokenizer(text=subtext, return_tensors="pt").to(self.device)
      with torch.no_grad():
        outputs = self.model(input_ids=inputs["input_ids"], speaker_id=speaker_id)
        wav = np.append(wav, outputs.waveform[0].cpu())

    return wav
