import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel, BitsAndBytesConfig, TextIteratorStreamer
from threading import Thread
import re
import numpy as np
import json
import subprocess

class inputFormatter:
  def __init__(self, template_example):
    sys_pos = re.search("システムプロンプト", template_example)
    u1_pos = re.search("ユーザ発言1", template_example)
    a1_pos = re.search("アシスタント発言1", template_example)
    u2_pos = re.search("ユーザ発言2", template_example)
    a2_pos = re.search("アシスタント発言2", template_example)

    self.t_sysprompt_user = template_example[0:a1_pos.start()].replace("システムプロンプト", r"{0}").replace("ユーザ発言1", r"{1}")
    self.t_sysprompt_user_assistant = template_example[0:a1_pos.end()].replace("システムプロンプト", r"{0}").replace("ユーザ発言1", r"{1}").replace("アシスタント発言1", r"{2}")
    self.t_user = template_example[a1_pos.end():a2_pos.start()].replace("ユーザ発言2", r"{0}")
    self.t_assistant = template_example[a2_pos.start():].replace("アシスタント発言2", r"{0}")

  def __call__(self, text, context, sysprompt=""):
    if(len(context) == 0):
      res = self.t_sysprompt_user.format(sysprompt, text)
    else:
      user_msgs = context[::2]
      assistant_msgs = context[1::2]

      try: 
        assert set([x["role"] for x in user_msgs]) == set(["user"]), "The roles of the context should be user, system, user..."
        assert set([x["role"] for x in assistant_msgs]) == set(["assistant"]), "The roles of the context should be user, system, user..."
        assert len(user_msgs)==len(assistant_msgs), "User and assistant messages should have equal lengths"

      except AssertionError as e:
        print(f"AssertionError: {e}")
        print("context = ", end="")
        print(context)

      res = self.t_sysprompt_user_assistant.format(sysprompt, user_msgs[0]["content"], assistant_msgs[0]["content"])

      for idx in range(1,len(user_msgs)):
        res += self.t_user.format(user_msgs[idx]["content"])
        res += self.t_assistant.format(assistant_msgs[idx]["content"])

      res += self.t_user.format(text)

    return res

class chatAIConfig:
  def __init__(self, config_dict):
    if type(config_dict) is str:
      with open(config_dict, "r", encoding="utf-8") as f:
        config_dict = json.load(f)

    assert type(config_dict) == dict, "config_dict should be either a dictionary or a path to a json file"

    self.model_id = config_dict["model_id"]

    try:
      self.model_name = config_dict["model_name"]
    except:
      self.model_name = self.model_id

    try: 
      self.tokenizer_id = config_dict["tokenizer_id"]
    except:
      self.tokenizer_id = self.model_id

    try:
      self.is_gptq = config_dict["is_gptq"]
    except:
      self.is_gptq = False

    try:
      self.use_safetensors = config_dict["use_safetensors"]
    except:
      self.use_safetensors = False

    self.use_fast_tokenizer = config_dict["use_fast_tokenizer"]
    self.generation_configs = config_dict["generation_configs"]
    self.load_in_4bit = config_dict["load_in_4bit"]
    self.template_example = config_dict["template_example"]
    self.sysprompt = config_dict["system_prompt"]

class chatAI:
  def __init__(self, config_dict):
    self.config = chatAIConfig(config_dict)
    self.formatter = inputFormatter(self.config.template_example)

    if self.config.load_in_4bit:
      self.bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
      )
    else:
      self.bnb_config = BitsAndBytesConfig(load_in_4bit=False)

    self.tokenizer = AutoTokenizer.from_pretrained(self.config.tokenizer_id, use_fast=self.config.use_fast_tokenizer)
    self.streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True)

    if self.config.is_gptq:
      from auto_gptq import AutoGPTQForCausalLM
      self.model = AutoGPTQForCausalLM.from_quantized(self.config.model_id, device_map="auto", use_safetensors=self.config.use_safetensors)

    else:
      self.model = AutoModelForCausalLM.from_pretrained(self.config.model_id, quantization_config=self.bnb_config, device_map="auto", use_safetensors=self.config.use_safetensors)

    self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
    self.context = []

  def reset(self):
    self.context = []

  def chat(self, text):
    input_text = self.formatter(text, self.context, self.config.sysprompt)
    inputs = self.tokenizer(input_text, return_tensors="pt").to(self.device)

    generation_kwargs = dict(inputs, **self.config.generation_configs, streamer=self.streamer)
    try:
      with torch.no_grad():
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs) 
        thread.start()

      generated_text = ""
      buff = ""
      for new_text in self.streamer: 
        if not new_text:
          continue

        generated_text += new_text
        buff += new_text

        subtexts = re.split(r"(。|？|！|\!|\?)", buff)
        if len(subtexts) > 2:
          subtext = "".join(subtexts[0:2])
          buff = "".join(subtexts[2:])
   
          yield subtext.strip(self.tokenizer.eos_token)
       
      yield buff.strip(self.tokenizer.eos_token)
      self.context.append({"role": "user", "content": text})
      self.context.append({"role": "assistant", "content": generated_text})

    except RuntimeError as e:
      print(e)
