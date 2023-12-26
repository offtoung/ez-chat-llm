class pageStyle:
  def global_css(self):
    css = ".gradio-container { height 90vh; width 90vw;}"
    css += "\n" + "footer {visibility: hidden}"
    css += "\n" + "#chat_history .message-bubble-border { border-style: none !important; padding: 0.5em 0.5em !important; margin: 0.5em 0em -1em 0em !important}"
    css += "\n" + "#chat_history { background-color: rgba(242, 242, 176, 0.6) !important}"
    css += "\n" + "#chat_history .bot { background-color: white !important; color: black !important;}"
    css += "\n" + "#chat_history .user { background-color: rgba(0, 123, 187, 1.0) !important; color: white !important;}"

    css += "\n" + "#submit_button { background: rgba(0, 123, 187, 1.0) !important; color: white !important;}"
    css += "\n" + "#revert_button { background: rgba(2, 135, 96, 1.0) !important; color: white !important;}"
    css += "\n" + "#reset_button { background: rgba(211, 56, 28, 1.0) !important; color: white !important;}"

    css += "\n" + "#figure .generating {border-style: none !important}"
    mycolor1 = "rgba(193,180,255,0.08)"
    mycolor2 = "rgba(255,255,255,0.08)"

    css += "\n" + "#main_screen { background-image: repeating-linear-gradient(45deg, mycolor1 25%, transparent 25%, transparent 75%, mycolor1 75%, mycolor1), repeating-linear-gradient(45deg, mycolor1 25%, mycolor2 25%, mycolor2 75%, mycolor1 75%, mycolor1); background-size: 60px 60px; background-position: 0 0, 30px 30px; background-color: mycolor2; }".replace("mycolor1", mycolor1).replace("mycolor2", mycolor2)

    return css

  def global_js(self):
    return '''async () => {
              res = await fetch("/file=configs/emotion/emotions.json");
              res_json = await res.json();
              globalThis.emo_dic = res_json;
              globalThis.eyeState = "openEyes";
              globalThis.currentEmotion = "基本";

              console.log(globalThis.currentEmotion); 
              console.log(globalThis.eyeState); 

              globalThis.updateFigure = () => {
                    document.getElementById("figure").src = "/file="+globalThis.emo_dic[globalThis.currentEmotion][globalThis.eyeState];
              }

              globalThis.Blink = () => {
                if(globalThis.eyeState == "openEyes"){
                  globalThis.eyeState = "closedEyes"
                  globalThis.updateFigure()

                  setTimeout(globalThis.Blink, 100) 
                }else{
                  globalThis.eyeState = "openEyes"
                  globalThis.updateFigure()

                  let blinkInterval = 2000.0*Math.exp(Math.sqrt(-2.0*Math.log( 1-Math.random() ))*Math.cos( 2.0*Math.PI*Math.random() ))
                  setTimeout(globalThis.Blink, blinkInterval)
                }

              }
              setTimeout(globalThis.Blink, 500)
            }
           '''

  def figureHTML(self, figure_path):
    return '''<img id="figure" src="/file={0}">'''.format(figure_path)

  def updateEmotion_js(self):
    return '''(emotion) => {
                  globalThis.currentEmotion = emotion;
                  globalThis.updateFigure();
                }
           '''
