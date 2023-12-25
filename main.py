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
current_emotion = emo.emotions_dict['基本']
changed_figure = True
playing_audio = False
generating = False

eye_state = "openEyes"
blink_timer = 1
blink_resolution = 0.1

def updateFigure():
  fig = current_emotion[eye_state]
  return fig

def updateEyeState():
  global eye_state
  global blink_timer
  if eye_state == "openEyes":
    blink_timer -= blink_resolution

    if blink_timer < 0:
      eye_state = "closedEyes" 
      blink_timer = blink_resolution

  else: 
    eye_state = "openEyes"
    blink_timer = np.random.exponential(scale=3.0)

  return eye_state

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

def sendMessage(text, output_text, chat_history):
  global generating
  global current_emotion

  if generating:
    return output_text, chat_history
  else:
    response_text = ""
    buff = ""
    generating = True
    
    response_text = ""
    for new_text in llm.chat(text):
      new_text = re.sub("\?", "？", new_text)
      new_text = re.sub("\!", "！", new_text)
      new_text = new_text.strip()

      response_text += new_text

    chat_history_arr.append([text, response_text])
    current_emotion = emo.get_emotion(response_text)
    generating = False

    return response_text, chat_history_arr

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
  if generating or playing_audio:
    return text, text
  else:
    return "", text

def prepareGUI():
  with gr.Blocks(css=styles.global_css()) as demo:
    with gr.Row(elem_id="main_screen"):
      figure = gr.Image(updateFigure, scale=1, show_download_button=False, container=False, every=blink_resolution, elem_id="figure")
      chat_history = gr.Chatbot([], container=False, min_width=50, scale=3, layout='bubble', elem_id="chat_history", bubble_full_width=False)
      with gr.Column(scale=1, min_width=50):
        llm_selector = gr.Dropdown(choices=llm_candidates, value=default_llm_select, elem_id="menu", label="対話モデル", interactive=True)
        voice_selector = gr.Dropdown(choices=voice_candidates, value=default_voice_select, elem_id="menu", label="音声モデル", interactive=True)
        reset_btn = gr.Button(value="会話をリセット", elem_id="reset_button")
        revert_btn = gr.Button(value="一つ戻す", elem_id="revert_button")

    with gr.Row(equal_height=True):
      with gr.Column(scale=10, min_width=80):
        #input_textbox = gr.Textbox("", container=True, label="Shift+Enter で改行", autofocus=True, elem_id="input_textbox")
        input_textbox = gr.Textbox("", container=True, label="Shift+Enter で改行", autofocus=False, elem_id="input_textbox")
      with gr.Column(scale=1, min_width=80):
        submit_btn = gr.Button(value="送信", elem_id="submit_button")
   
    with gr.Accordion(label="音声再生", open=False):
      voice = gr.Audio(generateVoice("こんにちは"), autoplay=True, visible=True, elem_id="voice")

    focus_js = '''() => document.getElementById("input_textbox").getElementsByTagName("textarea").item(0).focus()'''

    input_text_dummy = gr.Textbox("", visible=False, container=False)
    output_text = gr.Textbox("", visible=False, container=False)
    eye_state = gr.Textbox(updateEyeState, visible=False, container=False, every=0.1)

    submit_btn.click(
        fn=refreshInput, inputs=[input_textbox], outputs=[input_textbox, input_text_dummy], show_progress=False
    ).then(
        fn=sendMessage, inputs=[input_text_dummy, output_text, chat_history], outputs=[output_text, chat_history], show_progress=False
    ).then(
        fn=generateVoice, inputs=[output_text], outputs=[voice], show_progress=False
    ).then( 
        fn=None, js=focus_js
    )

    input_textbox.submit(
        fn=refreshInput, inputs=[input_textbox], outputs=[input_textbox, input_text_dummy], show_progress=False
    ).then(
        fn=sendMessage, inputs=[input_text_dummy, output_text, chat_history], outputs=[output_text, chat_history], show_progress=False
    ).then(
      fn=generateVoice, inputs=[output_text], outputs=[voice], show_progress=False
    ).then( 
        fn=None, js=focus_js
    )

    llm_selector.change(fn=reloadLLM, inputs=[llm_selector], outputs=[llm_selector]).then(fn=None, js=focus_js)

    voice_selector.change(fn=reloadVoiceModel, inputs=[voice_selector], outputs=[voice_selector]).then(fn=None, js=focus_js)

    revert_btn.click(fn=revertChat, inputs=None, outputs=[chat_history]).then(fn=None, js=focus_js)
    reset_btn.click(fn=resetChat, inputs=None, outputs=[chat_history]).then(fn=None, js=focus_js)

  demo.queue()
  return demo

if __name__ == '__main__':
  demo = prepareGUI()
  demo.launch(server_name="0.0.0.0", prevent_thread_lock=True, show_error=True)

  try:
    print("")
    input("Enter を押すと終了します")
  except KeyboardInterrupt:
    print("アプリケーションを終了しています...")

