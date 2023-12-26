from __future__ import annotations
import gradio as gr
import numpy as np
from typing import Iterable
import time
import re
import random
from modules import chatAI, chatAIConfig
from modules import ezttsModel, ezttsConfig
from modules import emotionManager
from styles import pageStyle
import os

import json

chat_history_arr = []
styles = pageStyle()
default_res = ""

default_llm_conf = "./configs/llm/tsukuyomi-chan-calm2-7b.json"
default_voice_conf = "./configs/voice/tsukuyomi-chan-vits.json"

default_llm_select = chatAIConfig(default_llm_conf).model_name
default_voice_select = ezttsConfig(default_voice_conf).model_name

llm = chatAI(default_llm_conf)
tts_model = ezttsModel(default_voice_conf)

llm_conf_dir = "./configs/llm/"
voice_conf_dir = "./configs/voice/"

llm_conffiles = [x for x in os.listdir(llm_conf_dir) if x[-4:] == "json"]
llm_candidates = sorted([chatAIConfig(llm_conf_dir+x).model_name for x in llm_conffiles])
llm_candidate_dict = {chatAIConfig(llm_conf_dir+x).model_name: llm_conf_dir+x for x in llm_conffiles}

voice_conffiles = [x for x in os.listdir(voice_conf_dir) if x[-4:] == "json"]
voice_candidates = sorted([ezttsConfig(voice_conf_dir+x).model_name for x in voice_conffiles])
voice_candidate_dict = {ezttsConfig(voice_conf_dir+x).model_name: voice_conf_dir+x for x in voice_conffiles}

emo = emotionManager("./configs/emotion/emotions.json")
changed_figure = True
eye_state = "openEyes"
playing_audio = False
generating = False

default_figure = emo.emotions_dict["基本"][eye_state]

def reloadVoiceModel(model_name, progress=gr.Progress()):
  global tts_model

  progress(0, desc="モデルを読み込んでいます...")
  tts_model = ezttsModel(voice_candidate_dict[model_name])
  progress(1, desc="モデルの読み込みを完了しました")
  return model_name

def reloadLLM(model_name, progress=gr.Progress()):
  global llm

  progress(0, desc="モデルを読み込んでいます...")
  progress(0, desc="モデルを読み込んでいます...")
  llm = chatAI(llm_candidate_dict[model_name])
  progress(1, desc="モデルの読み込みを完了しました")

  return model_name

def generateVoice(text):
  wav = tts_model.tts(text)
  return tts_model.sampling_rate, wav

def sendMessage(text, output_text, chat_history, emotion):
  global generating
  global playing_audio

  if generating:
    return output_text, chat_history, emotion
  else:
    chat_history_arr.append([text, "..."])
    yield output_text, chat_history_arr, emotion
    new_emotion = emotion
    response_text = ""
    buff = ""
    generating = True
    playing_audio = False
    
    response_text = ""
    buff = ""
    out_text = ""
    prev_out_text = ""

    for new_text in llm.chat(text):
      new_text = re.sub("\?", "？", new_text)
      new_text = re.sub("\!", "！", new_text)
      new_text = new_text.strip()

      response_text += new_text
      buff += new_text

      splitted = re.split(r"(\n|。)", buff)
      if len(splitted) >= 3:
        out_text += "".join(splitted[:2])
        buff = "".join(splitted[2:])
        chat_history_arr[-1] = [text, response_text]

        if playing_audio:
          yield prev_out_text, chat_history_arr, new_emotion
        else:
          new_emotion = emo.get_emotion(response_text)
          playing_audio = True
          yield out_text, chat_history_arr, new_emotion
          prev_out_text = out_text
          out_text = ""

    chat_history_arr[-1] = [text, response_text]
    if len(buff) > 0:
      out_text += buff

    if playing_audio:
      yield prev_out_text, chat_history_arr, new_emotion

    timer = 0
    if len(response_text) > 30:
       new_emotion = emo.get_emotion(response_text[:30])
    else:
      new_emotion = emo.get_emotion(response_text)
    if len(out_text) > 0:
      while playing_audio:
        timer += 0.01
        time.sleep(0.01)
        if timer > 60:
          break

      playing_audio = True
      yield out_text, chat_history_arr, new_emotion

    generating = False

def revertChat():
  global llm
  global chat_history_arr

  if len(llm.context) > 2 and len(chat_history_arr) > 1:
    llm.context = llm.context[:-2]
    chat_history_arr = chat_history_arr[:-1]
  else:
    llm.context = []
    chat_history_arr = []

  return chat_history_arr

def resetChat():
  global llm
  global chat_history_arr

  llm.context = []
  chat_history_arr = []

  return chat_history_arr

def refreshInput(text):
  if generating:
    return text, text
  else:
    return "", text

def stoppedVoice():
  global playing_audio
  playing_audio = False

def prepareGUI():
  with gr.Blocks(css=styles.global_css()) as demo:
    with gr.Row(elem_id="main_screen"):
      figure = gr.HTML(styles.figureHTML(default_figure))
      chat_history = gr.Chatbot([], container=False, min_width=50, scale=3, layout='bubble', elem_id="chat_history", bubble_full_width=False)
      with gr.Column(scale=1, min_width=50):
        llm_selector = gr.Dropdown(choices=llm_candidates, value=default_llm_select, elem_id="menu", label="対話モデル", interactive=True)
        voice_selector = gr.Dropdown(choices=voice_candidates, value=default_voice_select, elem_id="menu", label="音声モデル", interactive=True)
        reset_btn = gr.Button(value="会話をリセット", elem_id="reset_button")
        revert_btn = gr.Button(value="一つ戻す", elem_id="revert_button")

    with gr.Row(equal_height=True):
      with gr.Column(scale=10, min_width=80):
        input_textbox = gr.Textbox("", container=True, label="Shift+Enter で改行", autofocus=False, elem_id="input_textbox")
      with gr.Column(scale=1, min_width=80):
        submit_btn = gr.Button(value="送信", elem_id="submit_button")
   
    with gr.Accordion(label="音声再生", open=False):
      voice = gr.Audio(generateVoice("こんにちは"), autoplay=True, visible=True, elem_id="voice")

    focus_js = '''() => document.getElementById("input_textbox").getElementsByTagName("textarea").item(0).focus()'''

    input_text_dummy = gr.Textbox("", visible=False, container=False)
    output_text = gr.Textbox("", visible=False, container=False)
    eye_state = gr.Textbox("eyesOpen", visible=False, container=False)
    current_emotion = gr.Textbox("基本", visible=False, container=False)

    submit_btn.click(
        fn=refreshInput, inputs=[input_textbox], outputs=[input_textbox, input_text_dummy], show_progress=False
    ).then(
        fn=sendMessage, inputs=[input_text_dummy, output_text, chat_history, current_emotion], outputs=[output_text, chat_history, current_emotion], show_progress=False
    ).then( 
        fn=None, js=focus_js
    )


    input_textbox.submit(
        fn=refreshInput, inputs=[input_textbox], outputs=[input_textbox, input_text_dummy], show_progress=False
    ).then(
        fn=sendMessage, inputs=[input_text_dummy, output_text, chat_history, current_emotion], outputs=[output_text, chat_history, current_emotion], show_progress=False
    ).then( 
        fn=None, js=focus_js
    )

    output_text.change(fn=generateVoice, inputs=[output_text], outputs=[voice], show_progress=False).then(fn=None, js=styles.updateEmotion_js(), inputs=[current_emotion], show_progress=False)

    llm_selector.change(fn=reloadLLM, inputs=[llm_selector], outputs=[llm_selector]).then(fn=None, js=focus_js)

    voice_selector.change(fn=reloadVoiceModel, inputs=[voice_selector], outputs=[voice_selector]).then(fn=None, js=focus_js)

    revert_btn.click(fn=revertChat, inputs=None, outputs=[chat_history]).then(fn=None, js=focus_js)
    reset_btn.click(fn=resetChat, inputs=None, outputs=[chat_history]).then(fn=None, js=focus_js)

    voice.stop(fn=stoppedVoice)

    demo.load(None,None,None,js=styles.global_js())

  demo.queue()
  return demo

if __name__ == '__main__':
  demo = prepareGUI()

  demo.launch(server_name="0.0.0.0", allowed_paths=["figures", "configs/emotion"], prevent_thread_lock=True, share=True, show_error=True)

  try:
    print("")
    input("Enter を押すと終了します")
  except KeyboardInterrupt:
    print("アプリケーションを終了しています...")

