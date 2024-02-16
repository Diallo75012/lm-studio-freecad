from openai import OpenAI
import matplotlib.image as mpimg
import base64
import os
import sys
import datetime
import time
from taskweaver.plugin import Plugin, register_plugin


# check available plugins and use the right one to generate a 3D cube image

@register_plugin
class FreecaDrawing(Plugin):

  #################### SERVERS #################
  # LMStudio Server
  client_vision = OpenAI(base_url="http://192.168.186.139:1234/v1", api_key="not-needed")
  client_coder = OpenAI(base_url="http://0.0.0.0:1235/v1", api_key="not-needed")
  client_judge_code = OpenAI(base_url="http://0.0.0.0:1235/v1", api_key="not-needed")

  #################### VARS #################
  # variable storing all previous codes with errors  and all to get last one when code is working fine
  retries = 1
  timeout_seconds = 300
  sleep_time = 60
  temperature = 0.7
  freecad_all_codes_snippets = []

  #################### CALL MAIN FUNCTION #################
  def __call__(self, designer_need: str):
    self.designer_need = designer_need
    self.freecad_automation(self.designer_need, self.retries)


  #################### HELPER FUNCTIONS #################
  def freecad_script_execution(llm_made_script):
    self.llm_made_script = llm_made_script
    with open("taskweaver_freecad_automation_script.py", "w") as f:
      f.write(self.llm_made_script)
    return os.system(f"/home/creditizens/freecad_lm-studio/freecadus/AppRun freecadcmd /home/creditizens/freecad_lm-studio/freecadus/taskweaver_freecad_automation_script.py")

  # check if image exist at path
  def check_image_exists(self,image_path):
    self.iamge_path = image_path
    return os.path.exists(image_path)

	# fucntion to encode image to send to vision llm
  def encode_image(self, img_path):
    self.img_path = img_path
    with open(self.img_path.replace("'", ""), "rb") as img_file:
      self.img_file = img_file
      return base64.b64encode(self.img_file.read()).decode("utf-8")

	# Code error prompt template that will pass in the FreeCAD error
  def code_error_prompt_template(self, freecad_console_err):
    self.freecad_console_err = freecad_console_err
    return f"""
      There were an error output fromt he FreeCAD console which say:
      '{self.freecad_console_err}'
      Instructions:
        1. Analyze the previous code that you have provided to improve it and fix this error: '{self.freecad_console_err}'.
        2. Do not use variables or objects not available in FreeCAD. Use only FreeCAD libraries in your imports
        3. Make sure that the Python script part is in one block in Python markdown starting with ```python and closing with ```
        4. Make sure the code have good indentation and not lot of tabulation or spaces that makes the code impossible to execute.
		  """

  #################### CODERS FUNCTIONS  #################
  # Judge LLM Call
  def judge_call(self, prompt_user, code, error):
    # global timeout_seconds, sleep_time
    self.prompt_user = prompt_user
    self.code = code
    self.error = error
    self.completion_judge_call = ""
    self.response_judge_call = ""
		
    try:
      self.start_time = time.time()
      self.completion_judge_call = self.client_judge_code.chat.completions.create(
        model="local-model",
        messages=[
          {
            "role": "system",
            "content": f"""
              You are an expert in FreeCAD Python scripting and will help debug the code provided by the user by analyzing it to understand why it is not working.
              Instructions:
                1. Analyze the code provided by the user and the error. Check if the code has some other potential errors. No need to output your thought process.
                2. Provide only a full Python script in one block of Python markdown starting with ```python  and ending with ```
                3. Don't need to comment around the code or explanation, just provide the Python script. User don't need instructions, just needs the script as it is executed by the FreeCAD Python console.
                4. Respect user wanted file name for the picture and location where to save it.
             Here is user initial query:
                - '{self.prompt_user}'
          """
          },
          {
            "role": "user",
            "content": f"""
              My client wanted me to create a FreeCAD Python script to draw a 3D donut and download the file as png file 
              at a specific location '/tmp/donut_image.png'.
              My client request initial request: '{self.user_prompt}'.
              The issue is that the FreeCAD console when executing my code has shown some error: '{error}'
              Please help me fix my code and provide me a Python markdown synthaxed code. My code to be debugged:
              '{code}'
            """
          }
        ],
        temperature=self.temperature,
      )

      self.response_judge_call = self.completion_judge_call.choices[0].message.content.split("```")[1].strip("python").strip()

      while self.completion_judge_call.choices[0].message.function_call == None and self.completion_judge_call.choices[0].message.content == "." and (time.time() - self.start_time) < self.timeout_seconds:
        print("waiting for response")
        time.sleep(self.sleep_time)

      self.freecad_all_codes_snippets.append(f"{self.response_judge_call}")
      # exec(self.response_judge_call)
      self.freecad_script_execution(self.response_judge_call)

    except Exception as e:
      self.e = e
      raise self.e


  # function calling coder with error prompt template
  def calling_fixerror_coder(self, user_prompt_reminder, freecad_console_error):
    # global timeout_seconds, sleep_time
    self.user_prompt_reminder = user_prompt_reminder
    self.freecad_console_error = freecad_console_error
    self.error_notification_prompt_tenplate = ""
    self.response_fix_error_coder = ""
    
    try:
      self.start_time = time.time()
      self.error_notification_prompt_template = self.code_error_prompt_template(self.freecad_console_error)
      self.completion_fixerror_coder_call = self.client_coder.chat.completions.create(
        model="local-model",
        messages=[
          {
            "role": "system",
            "content": f"""
              Take the role of an expert FreeCAD Python scripting debugger and fix the previous code generated.
              Instruction:
                1. Analyze the error message and fix the code. 
                2. Do not explain anything, or give links, just provide the code it is for FreeCAD Python console to execute it.
                3. Create the full FreeCAD Python script in one block Python markdown starting with ```python and ending with ```
                4. Provide full code again fixed so that user can have what he is asking for.
                5. Respect user wanted file name for the picture and location where to save it.
              The original user request was:
                '{self.user_prompt_reminder}'
              """
          },
          {
            "role": "user",
            "content": f"""
              Here is the FreeCAD Python console error message after having executed the previous script that you provided:
                -'{self.error_notification_prompt_template}'.
              Please help me fix the error and do not invent libraries that are not in FreeCAD or objects that are not in FreeCAD. Fix the error.
             """
          }
        ],
        temperature=self.temperature,
      )
		  
      self.response_fixerror_coder = self.completion_fixerror_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()

      while self.completion_fixerror_coder_call.choices[0].message.function_call == None and self.completion_fixerror_coder_call.choices[0].message.content == "." and (time.time() - self.start_time) < self.timeout_seconds:
        print("waiting for response")
        time.sleep(self.sleep_time)
      
      self.freecad_all_codes_snippets.append(f"{self.response_fixerror_coder}")
      # exec(self.response_fixerror_coder)
      self.freecad_script_execution(self.response_fixerror_coder)

    except Exception as e:
      self.e = e
      try:
        self.judge_call(self.response_fixerror_coder,self.e)
      except Exception as err:
        self.err = err
        raise self.err
      raise self.e


  # Coder LLM Call
  def coder_call(self, user_prompt):
    # global timeout_seconds, sleep_time
    self.user_prompt = user_prompt
    self.completion_coder_call = ""
    self.response_coder = ""

    try:
      self.start_time = time.time()
      self.completion_coder_call = self.client_coder.chat.completions.create(
        model="local-model",
        messages=[
          {
            "role": "system",
            "content": f"""You take the role of a FreeCAD 3D Expert and will provide python scripts in markdown syntaxe that ready to be executed using ONLY FreeCAD libraries. The syntaxe is adaptated to the version of FreeCAD used by the user and at the end of the script it is downloaded a .png file from that drawing. 
               To complete this task:
                 1. Understand what FreeCAD version the user is talking about to avoid code errors. Don't output your thought process, user only need the code, no explanations.
                 2. Output only the full script Python markdown starting with ```python  and ending with ```
                 3. Do not explain the code or give links, user just need the python script.
                 4. Make sure to not invent libraries or properties that are not available on FreeCAD Python scripting.
                 5. To render the image use ONLY native FreeCAD libraries using (ActiveDocument,FreeCADGui, saveImage...etc...)
                 6. Make sure to understand where the user want the image to be saved.
             """
          },
          {
            "role": "user",
            "content": "{self.user_prompt}"
          }
        ],
        temperature=self.temperature,
        stream=False,
      )

      self.response_coder = self.completion_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()

      while self.completion_coder_call.choices[0].message.function_call == None and self.completion_coder_call.choices[0].message.content == "." and (time.time() - self.start_time) < self.timeout_seconds:
        print("Waiting for response")
        time.sleep(self.sleep_time)

      self.freecad_all_codes_snippets.append(f"{self.response_coder}")
      # exec(self.response_coder)
      self.freecad_script_execution(self.response_coder)

    except Exception as e:
      self.e = e
      try:
        self.judge_call(self.user_prompt, self.response_coder,self.e)
      except Exception as err:
        self.err = err
        raise self.err
      raise self.e
      

  #################### BUSINESS LOGIC FUNCTION: MAIN FUNCTION #################

  ### Use all function for business logic
  def freecad_automation(self, prompt, retries):
    # global timeout_seconds, sleep_time
    self.prompt = prompt
    self.retry_credit = retries
    while self.retry_credit > 0:
      # check if image exists
      if check_image_exists("/tmp/donut_image.png") == True:
        self.last_script_executed = self.freecad_all_codes_snippets[-1]
        return f"{'Success': The image of the place is already present at /tmp/donut_image.png}.\n Last script executed successfully was: ```python{self.last_script_executed}```"

      try:
        self.coder_call(self.prompt)
        #time.sleep(sleep_time)
      except (ImportError, SyntaxError, AttributeError) as e:
        self.e = e
        self.calling_fixerror_coder(self.prompt, self.e)
        self.retry_credit -= 1
        #time.sleep(sleep_time)
      except Exception as err:
        self.err = err
        self.calling_fixerror_coder(self.prompt, self.err)
        self.retry_credit -= 1
        #time.sleep(sleep_time)
      else:
        self.calling_fixerror_coder(self.prompt, f"""
          The Code Provided For User Query Didn't Work, 
          No Image Downloaded at path /tmp/donut_image.png. 
          Please provide only script without explanation for user to get his donut image. 
          User inital prompt was: '{self.prompt}'.
        """)
        self.retry_credit -= 1
        #time.sleep(sleep_time)

    return f"All retry credit have been used. Retry credit = {self.retry_credit}\n, Please discuss the code and why it is not doing what the user have asked for ('{self.prompt} and try again to use this plugin to call llm by adapting the user prompt and being more pecise.\n This is the last code executed that might have some error: ```python{self.freecad_all_codes_snippets[-1]}```')"
