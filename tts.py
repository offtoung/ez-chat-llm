import gradio as gr
import numpy as np
from modules import ezttsModel, ezttsConfig
from styles import pageStyle
import os

styles = pageStyle()

default_voice_conf = "./configs/voice/tsukuyomi-chan-vits.json"
default_voice_select = ezttsConfig(default_voice_conf).model_name

tts_model = ezttsModel(default_voice_conf)

voice_conf_dir = "./configs/voice/"

voice_conffiles = [x for x in os.listdir(voice_conf_dir) if x[-4:] == "json"]
voice_candidates = sorted([ezttsConfig(voice_conf_dir+x).model_name for x in voice_conffiles])
voice_candidate_dict = {ezttsConfig(voice_conf_dir+x).model_name: voice_conf_dir+x for x in voice_conffiles}

playing_audio = False

def reloadVoiceModel(model_name, progress=gr.Progress()):
  global tts_model

  progress(0, desc="モデルを読み込んでいます...")
  tts_model = ezttsModel(voice_candidate_dict[model_name])
  progress(1, desc="モデルの読み込みを完了しました")
  return model_name

def generateVoice(text):
  wav = tts_model.tts(text)
  return tts_model.sampling_rate, wav

def prepareGUI():
  with gr.Blocks(css=styles.global_css()) as demo:
    with gr.Row():
      with gr.Column(scale=5, min_width=50): 
        voice = gr.Audio(generateVoice("こんにちは"), autoplay=True, visible=True, elem_id="voice")
      with gr.Column(scale=1, min_width=50):
        voice_selector = gr.Dropdown(choices=voice_candidates, value=default_voice_select, elem_id="menu", label="音声モデル", interactive=True)

    with gr.Row(equal_height=True):
      with gr.Column(scale=10, min_width=80):
        input_textbox = gr.Textbox("", container=True, lines=5, label="Enter で改行", autofocus=True, elem_id="input_textbox")
      with gr.Column(scale=1, min_width=80):
        submit_btn = gr.Button(value="送信", elem_id="submit_button")

    submit_btn.click(fn=generateVoice, inputs=[input_textbox], outputs=[voice], show_progress=True)
    input_textbox.submit(fn=generateVoice, inputs=[input_textbox], outputs=[voice], show_progress=True)
    voice_selector.change(fn=reloadVoiceModel, inputs=[voice_selector], outputs=[voice_selector])

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

