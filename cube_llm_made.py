from openai import OpenAI
import matplotlib.image as mpimg
import base64
import os
import sys
import datetime
import time
"""
try:
  from ollama import Client
except ModuleNotFoundError as e:
  os.system("pip install ollama")
  from ollama import Client
"""


# add your python libraries to FreeCAD to avoid error of not installed packages
# sys.path.append("/usr/lib/python3/dist-packages")
# sys.path.append("/home/creditizens/.local/lib/python3.10/site-packages")

#################### SERVERS #################

# LMStudio Server
client_vision = OpenAI(base_url="http://192.168.186.139:1234/v1", api_key="not-needed")
client_coder = OpenAI(base_url="http://0.0.0.0:1234/v1", api_key="not-needed")
client_judge_code = OpenAI(base_url="http://0.0.0.0:1234/v1", api_key="not-needed")

# ollama server
# client_judge_code = Client(host='http://localhost:11434')


#################### VARS #################

# variable storing all previous codes with errors  and all to get last one when code is working fine
retries = 3
temperature = 0.8
error_cumulate = []
freecad_code_to_debug = []
freecad_all_codes_snippets = []
timeout_seconds = 180
sleep_time = 60

#################### HELPER FUNCTIONS #################

# check if image exist at path
def check_image_exists(image_path):
    return os.path.exists(image_path)

# fucntion to encode image to send to vision llm
def encode_image(image_path):
  with open(image_path.replace("'", ""), "rb") as image_file:
    return base64.b64encode(image_file.read()).decode("utf-8")


# Code error prompt template that will pass in the FreeCAD error
def code_error_prompt_template(freecad_console_error):
  return f"""
    There were an error output fromt he FreeCAD console which say:
    '{freecad_console_error}'
    Instructions:
      1. Analyze the previous code that you have provided to improve it and fix this error: '{freecad_console_error}'.
      2. Do not use variables or objects not available in FreeCAD. Use only FreeCAD libraries in your imports
      3. Make sure that the Python script part is in one block in Python markdown starting with ```python and closing with ```
      4. Make sure the code have GOOD INDENTATION and not lot of tabulation or spaces that makes the code impossible to execute
    """
# Vison returned False, the image doesn't look like a cube, send comments to coder llm for it to have context for adjustment
def code_call_fixvision_prompt_template(vision_llm_comment, latest_code):
  with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
    file.write(f"{datetime.datetime.now()} Inside 'coder_call_fixvision_prompt_template': passing vision llm comment to format a prompt\n")

  return """
    The code has executed and we got the analyzed and it appears that the drawing is not a 3D cube.
    Here is the detailed comment message: '{vision_llm_comment}'
    Instructions:
      1. Analyze the comment message.
      2. Analyze the code and evaluate adjustment for the 2D image generated to look like a 3D object. (odject orientation, ordject centered so it renders fully, background contract to see the object).
    Here is the latest code produced that works fine and downloads the image but there seems to be visual issues with the final image:
      {lastest_code}
  """

#################### CODERS FUNCTIONS  #################
# Judge LLM Call
def judge_call(code, error):
  global error_cumulate, freecad_code_to_debug, freecad_all_codes_snippets, timeout_seconds, sleep_time, temperature

  completion_judge_call = ""
  response_judge_call = None
  try:
    start_time = time.time()
    completion_judge_call = client_judge_code.chat.completions.create(
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
              4. Make sure the code have GOOD INDENTATION and not lot of tabulation or spaces that makes the code impossible to execute.
              5. Respect user wanted file name for the picture and location where to save it.
            Here is user initial query:
              - 'I need a Python script to draw a 3D cube on FreeCAD version 0.21.2 and save the cube image as .png file at location /tmp/cube_image.png'
          """
        },
        {
          "role": "user",
          "content": f"""
            My client wanted me to create a FreeCAD Python script to draw a 3D cube and download the file as png file 
            at a specific location '/tmp/cube_image.png'.
            My client request initial request: 'I need  a Python script to draw a 3D cube on FreeCAD version 0.21.2 and save the cube image as .png file in the /tmp/ folder with filename cube_image.png'.
            The issue is that the FreeCAD console when executing my code has shown some error: '{error}'
            Please help me fix my code and provide me a Python markdown synthaxed code. My code to be debugged:
            '{code}'
          """
        }
      ],
      temperature=temperature,
    )

    while completion_judge_call.choices[0].message.function_call == None and completion_judge_call.choices[0].message.content == "." and (time.time() - start_time) < timeout_seconds:
        with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
          file.write(f"{datetime.datetime.now()} Inside 'Judge_call': Waiting for completion_judge_call\n")
        print(f"{datetime.datetime.now()} Inside 'judge_call': Waiting for completion_judge_call\n")
        time.sleep(sleep_time)

    response_judge_call = completion_judge_call.choices[0].message.content.split("```")[1].strip("python").strip()
    print("Got judge response")
    
    freecad_all_codes_snippets.append(f"{len(freecad_code_to_debug)}. Code from Judge_call: {response_judge_call}")

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_code.txt', 'a') as file:
      file.write(f"\n{datetime.datetime.now()}\n{response_judge_call}\n")    
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'Judge_call': Code execution in FreeCAD console Request Sent\n")
    print(f"{datetime.datetime.now()} Inside 'judge_call': Code execution in FreeCAD console\n")
   
    exec(response_judge_call)
  
  except (ImportError, SyntaxError, AttributeError, NameError) as e:
    freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error From judge_call'{e}': {response_judge_call}")
    error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")
    
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'Judge_call': Exception raised ImportError, SyntaxError, AttributeError, NameError: {e}\n")
    print(f"Inside Judge_call Exception raised ImportError, SyntaxError, AttributeError, NameError: {e}")
    
    #raise e
 
  except Exception as e:
    freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error From judge_call'{e}': {response_judge_call}")
    error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")
    
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'Judge_call': Exception raised: {e}\n")
    print(f"Inside Judge_call Exception raised: {e}")
    
    #raise e


# function calling coder with error prompt template
def calling_fixerror_coder(freecad_console_error):
  global error_cumulate, freecad_code_to_debug, freecad_all_codes_snippets, timeout_seconds, sleep_time, temperature

  error_notification_prompt_tenplate = ""
  response_fix_error_coder = ""
  try:
    start_time = time.time()
    error_notification_prompt_template = code_error_prompt_template(freecad_console_error)
    completion_fixerror_coder_call = client_coder.chat.completions.create(
    model="local-model",
    messages=[
        {
          "role": "system",
          "content": f"""
            Take the role of an expert FreeCAD Python scripting debugger and fix the previous code generated.
            Instruction:
              1. Analyze the error message and fix the code.
              2. Check if you haven't forgotten to provide a method or function.
              2. Do not explain anything, or give links, just provide the code it is for FreeCAD Python console to execute it.
              3. Make sure the code have GOOD INDENTATION and not lot of tabulation or spaces that makes the code impossible to execute.
              4. Create the full FreeCAD Python script in one block Python markdown starting with ```python and ending with ```
              5. Provide full code again fixed so that user can have what he is asking for.
              6. Respect user wanted file name for the picture and location where to save it.
            The original user request was:
              'I need a Python script to draw a 3D cube on FreeCAD version 0.21.2 and save the cube image as .png file at location /tmp/cube_image.png'
          """
        },
        {
         "role": "user",
          "content": f"""
          Here is the FreeCAD Python console error message after having executed the previous script that you provided:
            -'{error_notification_prompt_template}'.
          Please help me fix the error and do not invent libraries that are not in FreeCAD or objects that are not in FreeCAD. Fix the error.
          """
        }
      ],
      temperature=temperature,
    )

    while completion_fixerror_coder_call.choices[0].message.function_call == None and completion_fixerror_coder_call.choices[0].message.content == "." and (time.time() - start_time) < timeout_seconds:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside 'calling_fixerror_coder': Waiting for error_notification_prompt_template\n")
      print(f"{datetime.datetime.now()} Inside 'calling_fixerror_coder': Waiting for error_notification_prompt_template\n")
      time.sleep(sleep_time)

    response_fixerror_coder = completion_fixerror_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_code.txt', 'a') as file:
      file.write(f"\n{datetime.datetime.now()} \n{response_fixerror_coder}\n")
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'calling_fixerror_coder': code fix error received and applied to FreeCAD console\n")
    print(f"{datetime.datetime.now()} Inside 'calling_fixerror_coder': code fix error received executed in FreeCAD console\n")

    exec(response_fixerror_coder)
    freecad_all_codes_snippets.append(f"{len(freecad_code_to_debug)}. Code From 'calling_fixerror_coder': {response_fixerror_coder}")

  except Exception as e:
    freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error From Fixerror_coder'{e}': {response_fixerror_coder}")
    error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'calling_fixerror_coder': Exception raised: {e}\n")
    print(f"Inside calling_fixerror_coder Exception raised: {e}")

    try:
      judge_call(response_fixerror_coder,e)

      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside calling_fixerror_coder Exception Error of second try: {e}\njudge_call sent")
      print(f"Inside calling_fixerror_coder Exception Error of second try: {e}\njudge_call sent")

    except (ImportError, SyntaxError, AttributeError, NameError) as er:
      freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error from judge_coder '{er}': {response_fixerror_coder}")
      error_cumulate.append(f"Error ({len(error_cumulate)}): {er}")
      
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside calling_fixerror_coder Exception Error of second except ImportError, SyntaxError, AttributeError, NameError: {er}\n")
      print(f"Inside calling_fixerror_coder Exception Error of second try/except ImportError, SyntaxError, AttributeError, NameError: {er}")

      #raise er

    except Exception as er:
      freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error from judge_coder '{er}': {response_fixerror_coder}")
      error_cumulate.append(f"Error ({len(error_cumulate)}): {er}")
      
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside calling_fixerror_coder Exception Error of second except: {er}\n")
      print(f"Inside calling_fixerror_coder Exception Error of second try/except: {er}")

      #raise er
    #raise e


# function that calls coder when vision llm is not agree about result
def coder_call_fixvision(vision_comment_prompt_template):
  global error_cumulate, freecad_code_to_debug, freecad_all_codes_snippets, timeout_seconds, sleep_time, temperature

  completion_fixvision_coder_call = ""
  response_fixvision_coder = None
  try:
    start_time = time.time()
    completion_fixvision_coder_call = client_coder.chat.completions.create(
    model="local-model",
    messages=[
        {
          "role": "system",
          "content": f"""
            Take the role of an expert in FreeCAD Python scripting using FreeCADGui scripting abilities and just provide the small slightly code change fix to get the end result wanted as user is using Python console to execute the script and expecting to have a good render of the image at the end.
            User inital prompt was: 'I need a Python script to draw a 3D cube on FreeCAD version 0.21.2 and save the cube image as .png file at /tmp/cube_image.png'. But the issue is that the code worked but there is visual issues with the image generated.
          """
        },
        {
          "role": "user",
          "content": f"""
            Please apport small modification to the previous code which was successfully saving the image to address those little aspects commented when someone checked on the picture. Comment to address: {vision_comment_prompt_template}
          """
        }
      ],
      temperature=temperature,
      stream=False,
    )
    

    while completion_fixvision_coder_call.choices[0].message.function_call == None and completion_fixvision_coder.choices[0].message.content == "." and (time.time() - start_time) < timeout_seconds:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside 'coder_call_fixvision': Waiting for completion_fixvision_coder_call\n")
      print(f"{datetime.datetime.now()} Inside 'coder_call_fixvison': Waiting for completion_fixvision_coder_call\n")
      time.sleep(sleep_time)
    
    response_fixvision_coder = completion_fixvision_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()


    with open('/home/creditizens/freecad_lm-studio/freecad_automation_code.txt', 'a') as file:
      file.write(f"\n{datetime.datetime.now()}\n{response_fixvision_coder}\n")

    freecad_all_codes_snippets.append(f"{len(freecad_code_to_debug)}. Code From Fixvison_coder: {response_fixvision_coder}")
    exec(response_fixvision_coder)

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'coder_call_fixvision': code fix vision received and applied to FreeCAD console\n")
    print(f"{datetime.datetime.now()} Inside 'calling_fixerror_coder': code received and applied to FreeCAD console\n")

  except Exception as e:
    freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code From Calling_fixerror_coder: {response_fixvision_coder}")
    error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside calling_fixerror_coder Exception Error of second except: {e}\n")
    print(f"Inside coder_call_fixvision Exception Error of second try/except: {e}")

    #raise e

# Vision LLM Call
def vision_call():
  global error_cumulate, freecad_code_to_debug, freecad_all_codes_snippets, timeout_seconds, sleep_time
  
  cube_image_path = ""
  cube_image_base64 = ""
  cube_image_for_vision_llm = ""
  compeletion_vision_call = ""
  response = None
  vision_response = ""
  response_vision = ""
  response_vision_comment = ""
  try:
    cube_image_path = "/tmp/cube_image.png"
    cube_image_base64 = encode_image(cube_image_path)
    cube_image_for_vision_llm = f"data:image/png;base64,{cube_image_base64}"
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'vision_call': PNG converted to send to llm\n")

    completion_vision_call = client_vision.chat.completions.create(
      model="local-model",
      messages=[
        {
          "role": "system",
          "content": f'''This task involves creating a response to describe the content of an image and
                  tell if it is a cube or not. The response must be written in markdown format.
                  In this case, the instruction are:
                   To complete this task:
                    1. use 100 words at maximum to describe the image and tell why it is a cube or why it is not a cube in the image.
                    2. Create a response True or False in markdown format putting the answer between quotes like:
                     ```python <your answer True or False>```
                    3. Do not read file name to make your decision as it could be misleading with a different image representation not mathcing the name of the image.
             ''',
        },
        {
          "role": "user",
          "content": [
          {
            "type": "text",
            "text": f'''I have printed this image from FreeCAD and want you to tell me, what is in this image?
              Tell me if it is cube or not?
              If it is True, just respond one word True using Python markdown starting with ```python
              If it is not a cube provide a short comment of less than 100 words and respond just one word False using Python markdown starting with ```python.
              The total length of the answer should be less than 100 words. It is an automated system and only needs True or False and if False will parse the little comment in why you judge it False.
             '''
          },
          {
            "type": "image_url",
            "image_url": {
              "url" : f"{cube_image_for_vision_llm}",
            },
          }
          ]
        },
      ],
      max_tokens=1000,
      stream=False,
    )
    
    start_time = time.time()
    response = completion_vision_call.choices[0]

    while completion_vision_call.choices[0].message.function_call == None and completion_vision_call.choices[0].message.content == "." and (time.time() - start_time) < timeout_seconds:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside 'vision_call': Waiting for response of vision call\n")
      print(f"{datetime.datetime.now()} Inside 'vision_call': Waiting for response of vision call\n")
      time.sleep(sleep_time)

    response_vision = response.message.content.split("```")[1].strip("python").strip()
  
    if len(response.split("```")) > 2:
      response_vision_comment = response.message.content.split("```")[0].strip() + "/n" + " ".join(response.message.content.split("```")[2:])
    else:
      response_vision_comment = response.message.content.split("```python")[0].strip()
  
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'vision_call': Response received and parsed in two parts code and comment\n")
  
    vision_response = [
      {
        "response_vision": response_vision,
        "response_vision_comment": response_vison_comment
      }
    ]
    print(f"Vision Response: {vison_response}")
    return vision_response

  except Exception as e:
      error_cumulate.append(f"Error ({len(error_cumulate)}) 'From Image Vision LLM': {e}")

      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside vision_call Exception Error: {e}\n")
      print(f"Inside coder_call Exception Error: {e}")      
      raise e

# Coder LLM Call
def coder_call():
  global error_cumulate, freecad_code_to_debug, freecad_all_codes_snippets, timeout_seconds, sleep_time
  completion_coder_call = ""
  response_coder = ""

  try:
    start_time = time.time()
    completion_coder_call = client_coder.chat.completions.create(
      model="local-model",
      messages=[
        {
          "role": "system",
          "content": f'''You take the role of a FreeCAD 3D Expert and will provide python scripts in markdown syntaxe that ready to be executed using ONLY FreeCAD libraries. The syntaxe is adaptated to the version of FreeCAD used by the user and at the end of the script it is downloaded a .png file from that drawing. 
                   To complete this task:
                    1. Understand what FreeCAD version the user is talking about to avoid code errors. Don't output your thought process, user only need the code, no explanations.
                    2. Output only the full script Python markdown starting with ```python  and ending with ```
                    3. Make sure the code have GOOD INDENTATION and not lot of tabulation or spaces that makes the code impossible to execute.
                    4. Do not explain the code or give links, user just need the python script.
                    5. Make sure to not invent libraries or properties that are not available on FreeCAD Python scripting.
                    6. To render the image use ONLY native FreeCAD libraries using (ActiveDocument,FreeCADGui, saveImage...etc...)
                    7. Make sure to understand where the user want the image to be saved.
            '''
        },
        {
          "role": "user",
          "content": "I need a Python script to draw a 3D cube on FreeCAD version 0.21.2 and save the cube image as .png file at '/tmp/cube_image.png' location"
        }
      ],
      temperature=temperature,
      stream=False,
    )
    print("completion_coder_call", completion_coder_call)

    while completion_coder_call.choices[0].message.function_call == None and completion_coder_call.choices[0].message.content == "." and (time.time() - start_time) < timeout_seconds:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside 'coder_call': Waiting for completion_coder_call\n")
      print(f"{datetime.datetime.now()} Inside 'Coder_call': Waiting for completion_coder_call\n")
      time.sleep(sleep_time)
    
    response_coder = completion_coder_call.choices[0].message.content.split("```")[1].strip("python").strip()

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_code.txt', 'a') as file:
      file.write(f"\n{datetime.datetime.now()}\n{response_coder}\n")
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'coder_call': Code execution in FreeCAD console\n")
    print(f"{datetime.datetime.now()} Inside 'coder_call': Code execution in FreeCAD console\n")
    
    freecad_all_codes_snippets.append(f"{len(freecad_code_to_debug)}. Code From Coder_call: {response_coder}") 
    exec(response_coder)
    print("code_call code executed in FreeCAD console") 

  
  except Exception as e:
    freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error From coder_call'{e}': {response_coder}")
    error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")

    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'coder_call': Exception raised: {e}\n")
    print(f"Inside coder_call Exception raised: {e}")
    
    try:
      judge_call(response_coder,e)

      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside coder_call Exception Error of second try: {e}\njudge_call sent")
      print(f"Inside coder_call Exception Error of second try: {e}\njudge_call sent")

    except (ImportError, SyntaxError, AttributeError, NameError) as er:
      freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error From coder_call'{er}': {response_coder}")
      error_cumulate.append(f"Error ({len(error_cumulate)}): {er}")

      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside coder_call Exception Error of second except ImportError, SyntaxError, AttributeError, NameError: {er}\n")
      print(f"Inside coder_call Exception Error of second try/except ImportError, SyntaxError, AttributeError, NameError: {er}")

      #raise er    

    except Exception as er:
      freecad_code_to_debug.append(f"{len(freecad_code_to_debug)}. Code With Error From coder_call'{er}': {response_coder}")
      error_cumulate.append(f"Error ({len(error_cumulate)}): {er}")

      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside coder_call Exception Error of second except: {er}\n")
      print(f"Inside coder_call Exception Error of second try/except: {er}")

      #raise er
    #raise e
      

#################### BUSINESS LOGIC FUNCTION: MAIN FUNCTION #################

### Use all function for business logic
def freecad_automation(retries):
  global error_cumulate, freecad_code_to_debug, freecad_all_codes_snippets, timeout_seconds, sleep_time
  
  retry_credit = retries
  error_cumulate = error_cumulate
  freecad_code_to_debug = freecad_code_to_debug
  freecad_all_codes_snippets = freecad_all_codes_snippets

  with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
    file.write(f"\n\n\n{datetime.datetime.now()} Automation process started.\n")
  print(f"\n\n\n{datetime.datetime.now()} Automation process started.\n")

  while retry_credit > 0:
    # check if image exists
    if check_image_exists("/tmp/cube_image.png") == True:
      """
      vision_call = vision_call()
      # time.sleep(sleep_time)
      # if vision llm answers True then we stop the process and return a message with file location
      if (decision := vision_call[0]["response_vison"]) == 'True':
        with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
          file.write(f"{datetime.datetime.now()} Inside Loop Image Exist. Success image created and validated! Bravo!\n")
        return f"Success: The cube image is at path '/tmp/cube_image.png'. Decision of vision llm was: {decision}"
      else:
        with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
          file.write(f"{datetime.datetime.now()} Inside Loop Image Exist decision of vision llm is: {decision}. Therefore, calling coder_call_fixvision to fix it.\n")
        latest_code = f"{freecad_all_codes_snippets[-1]}"
        vision_comment = vision_call[0]["response_vision_comment"]
        vision_comment_prompt_template = code_call_fixvision_prompt_template(vision_comment, latest_code)
        coder_call_fixvision(vision_comment_promt_template)
        # time.sleep(sleep_time)
        print(f"{'message': 'Full round done with code fix after vision invalidation. Decision: {decision}'}")
      """
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()}: Automation ENDS! [{'Success': The image of the place is already present at /tmp/cube_image.png}]")
      print("{'Success': The image of the place is already present at /tmp/cube_image.png}")
      return "{'Success': The image of the place is already present at /tmp/cube_image.png}.\nHere all error {len(error_cumulate)} accumulated before getting image output: {error_cumulate}"

    try:

      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} calling coder_call fron loop Try\n")
      print(f"{datetime.datetime.now()} coder_call call sent from loop\n")
      
      retry_credit -= 1
      print(f"Number of error cumulated for the moment: {len(error_cumulate)}; Retry credit= {retry_credit}")
      print(f"Number of retry credit left: {retry_credit};  Error cumulated: {len(error_cumulate)}")
      
      coder_call()

      #time.sleep(sleep_time)

    except (ImportError, SyntaxError, AttributeError, NameError) as e:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside while loop calling_fixerror_coder Exception Import,Syntax,NameError or Attribute Error: {e}\n")

      retry_credit -= 1

      print(f"Number of retry credit left: {retry_credit};  Error cumulated: {len(error_cumulate)}")

      error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")
      calling_fixerror_coder(error_cumulate)

      #time.sleep(sleep_time)

    except Exception as e:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside 'While loop' Error:{e}.  calling_fixerror_coder function\n")
      print(f"{datetime.datetime.now()} Inside while loop Except/Exception calling to fix error: {e}")

      retry_credit -= 1
      
      print(f"Number of retry credit left: {retry_credit};  Error cumulated: {len(error_cumulate)}")    

      error_cumulate.append(f"Error ({len(error_cumulate)}): {e}")
      calling_fixerror_coder(error_cumulate)


      #time.sleep(sleep_time)     

    else:
      with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
        file.write(f"{datetime.datetime.now()} Inside 'While loop Else' no image found and no error catch: 'calling_fixerror_coder function' \n")
      print(f"{datetime.datetime.now()} Inside while loop 'else', no image found and no errors catch therefore 'calling_fixerror_coder function' ")
      
      retry_credit -= 1
      print(f"Number of retry credit left: {retry_credit};  Error cumulated: {len(error_cumulate)}")

      calling_fixerror_coder("""
        The Code Provided For User Query Didn't Work, 
        No Image Downloaded at path /tmp/cube_image.png. 
        Please provide only script without explanation for user to get his cube image. 
        User inital prompt was: 'I need a Python script to draw a 3D cube on FreeCAD version 0.21.2 and save the cube image as .png file at /tmp/cube_image.png'.
        """)
      #time.sleep(sleep_time)
  
    with open('/home/creditizens/freecad_lm-studio/freecad_automation_logs.txt', 'a') as file:
      file.write(f"{datetime.datetime.now()} Inside 'While loop Out of Try/except/else': retry credit = {retry_credit}\n")
  print(f""" LOOP DONE: [
    \nerror_cumulate : {error_cumulate[-1]},
    \nfreecad_code_to_debug : {freecad_code_to_debug[-1]},
    \nfreecad_all_codes_snippets : {freecad_all_codes_snippets[-1]}\n
    \nf"Total retry credit left: {retry_credit}; Total Error cumulated: {len(error_cumulate)}"\n
  ]
  """)
  return f"All retry credit have been used. Retry credit = {retry_credit}\nHere all errors not solved: {error_cumulate}"

freecad_automation(retries)



# Perfect Prompt From Taskweaver Init Plan
 1. create a new FreeCAD document
 2. insert a 3D cube object into the document
 3. save the FreeCAD document as .stl file
 4. convert the saved .stl file to .png format
 5. save the converted image at '/tmp/cube_image.png'
 6. report the result to the user <interactively depends on 1, 2, 3, 4, 5>
 
 
"""
# variable to create to have more dynamic code
user drawing request
file location
"""
