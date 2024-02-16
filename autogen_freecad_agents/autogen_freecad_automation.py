import autogen
import os

#from importlib.metadata import version as lib_version
#print("pyautogen version: " + lib_version("pyautogen"))

# create an AssistantAgent instance named "assistant"
#assistant = AssistantAgent(name="assistant")

# create a UserProxyAgent instance named "user_proxy"
#user_proxy = UserProxyAgent(name="user_proxy")

#### Client Configs setup

api_keys = ["NO_KEYS_NEEDED_IN_SHIBUYA_MANGAKISSA_DOORS_ARE_OPEN"]
 # lmstudio endpoint
base_urls = ["http://192.168.186.139:1234/v1"]
api_type = "openai"
api_version = None

config_list = autogen.get_config_list(api_keys, base_urls=base_urls, api_type=api_type, api_version=api_version)

"""
config_list = [
  {
    "api_type" : "openai",
    "api_base" : "http://192.168.186.139:1234/v1",
    "api_key"  : "NO_KEYS_NEEDED_IN_SHIBUYA_MANGAKISSA_DOORS_ARE_OPEN"
  }
]
"""

llm_config = {
  "config_list": config_list,
  "temperature": 0.7,
  "seed": 23,
  "functions":[
    {
      "name": "freecad_script_execution",
      "description": "Executes the Python script in the FreeCAD Python console",
      "parameters": {
        "type": "object",
        "properties": {
          "freecad_3d_cube_script_file_name":{
            "type": "string",
            "description": "The name of the FreeCAD Python script to be executed in the FreeCAD Python console. Example of a file name: 'freecad_cube_drawing.py'"
          }
        },
        "required": ["freecad_3d_cube_script_file_name"]
      }
    },
  ],
  "model": "gpt-4",
  "stream": False,
  "timeout": 300,
}

llm_config_group_chat = {
  "config_list": config_list,
  "temperature": 0.7,
  "seed": 23,
  "model": "gpt-4",
  "stream": False,
}



#### Agents Creation
coordinator = autogen.UserProxyAgent(
    name="coordinator",
    human_input_mode="NEVER",# "TERMINATE"
    max_consecutive_auto_reply=2,
    code_execution_config={"last_n_messages": 3, "work_dir":"/home/creditizens/freecad_lm-studio/freecadus/", "use_docker":False},
    llm_config=llm_config,
    system_message=""""Analyze the User request and work with 'coder' and 'codechecker' assistants. Execute code and see if image is present at path. Provide the final code that have worked with name of script and path location, and, the image name and path location. Reply TERMINATE only if image present at path location Otherwise reply CONTINUE and instruct other assistants to provide new code or to critic the code for improvements by showing them the error in your reply. Don't forget to reply always. Other agent assistant are 'coder' and 'codechecker'.
    """,
    default_auto_reply="coder provide a new code"
)


coder = autogen.AssistantAgent(
    name="coder",
    # human_input_mode="NEVER",# "TERMINATE"
    # max_consecutive_auto_reply=2,
    # code_execution_config={"last_n_messages": 3, "work_dir":"/home/creditizens/freecad_lm-studio/freecadus/", "use_docker":False},
    llm_config=llm_config,
    system_message=""""You are a FreeCAD Python console scripting expert and create code that user are asking for. You can create Python script ready to be executed to the FreeCAD Python console and create 3D objects in FreeCAD that are going to be exported as 2D '.png' file. Save the script to a file and ask 'coordinator' to use available function to execute it. It is a loop process, when an error is raise you will modify the script to make it work. Other agent assistant are 'coordinator' who executes code and 'codechecker' who criticize the code. Don't forget to reply always.
    """,
    default_auto_reply="Please execute the code using the function available, if .png image present at path reply TERMINATE otherwise Reply CONTINUE and send user query, code and FreeCAD console error to next assistant.Don't forget to reply always.Other agent assistant are 'coder' and 'coordinator'."
)

codechecker = autogen.AssistantAgent(
    name="codechecker",
    # human_input_mode="NEVER",# "TERMINATE"
    # max_consecutive_auto_reply=2,
    # code_execution_config={"last_n_messages": 3, "work_dir":"/home/creditizens/freecad_lm-studio/freecadus/", "use_docker":False},
    llm_config=llm_config,
    system_message=""""
    Critic expert in FreeCAD Python console scripting ability. Double check plan, claims, code from other agents and provide feedback. Check if the imports are correct, indentation, and all method called have their function in the code. Check if image is saved in the right folder. Check whether the plan outcoume will be met or not and provide advice.Don't forget to reply always. Other agent assistant are 'coordinator' to execute the code and 'coder' to provide a new code. Send your remarks to 'coder' if you want new code or to 'coordinator' if you believe it can be executed.
    """,
    default_auto_reply="Please execute the code using the function available, if .png image present at path reply TERMINATE otherwise Reply CONTINUE and send user query, code and FreeCAD console error to next assistant."
)

#### Helper function
def freecad_script_execution(freecad_3d_cube_script_file_name):
  import os
  return os.system(f"/home/creditizens/freecad_lm-studio/freecadus/AppRun freecadcmd /home/creditizens/freecad_lm-studio/freecadus/{freecad_3d_cube_script_file_name}")


for assistant in [coordinator, coder, codechecker]:
    # register functions for all agents.
    assistant.register_function(
        function_map={
            "freecad_script_execution": freecad_script_execution,
        }
    )

"""
codechecker.generate_reply(
  messages = [
    {
      "content": "Ok I will check how the requested script can be done the best way!",
      "name": "coordinator",
            "role": "user",
    },  
  ],
  sender = "coordinator",
)

codechecker.generate_reply(
  messages = [
    {
      "content": "Ok i will make the script work using only FreeCAD libraries.",
      "name": "coder",
      "role": "user",
    },  
  ],
  sender = "coder",
)

coder.generate_reply(
  messages = [
    {
      "content": "Ok i will make the script work using only FreeCAD libraries.",
      "name": "coordinator",
            "role": "user",
    },  
  ],
  sender = "coordinator",
)

coder.generate_reply(
  messages = [
    {
      "content": "Ok i will make the script work using only FreeCAD libraries.",
      "name": "codechecker",
      "role": "user",
    },  
  ],
  sender = "codechecker",
)

coordinator.generate_reply(
  messages = [
    {
      "content": "I will execute the code now. If the image is at the right location I will reply TERMINATE otherwise i will send you the FreeCAD console error and ask you to provide new script. Comply with user request and make this script work fine. User want to create a #D cube on FreeCAD using Python console script and download the file as '.png' named 'cube_image.png'",
      "name": "coder",
            "role": "user",
    },  
  ],
  sender = "coder",
)

coordinator.generate_reply(
  messages = [
    {
      "content": "Thank you for your critic, i will execute the code. If it works i will reply TERMINATE, if it doesn't work and have errors, i will send those errors to 'coder' assistant to fix those and provide new script.",
      "name": "codechecker",
      "role": "user",
    },  
  ],
  sender = "codechecker",
)
"""

"""
# codechecker_assistant execution of function by user_proxy
codechecker.register_function(
  function_map={
      "freecad_script_execution": freecad_script_execution,
    }
    #freecad_script_execution,
    #agent=codechecker_assistant,
    #executor=user_proxy,
    #description="Freecad Python console script executor. If execution fails try again with command: '/home/creditizens/freecad_lm-studio/freecadus/AppRun freecadcmd <Python script file>'",
)

# coder_assistant execution of function by user_proxy
coder.register_function(
  function_map={
      "freecad_script_execution": freecad_script_execution,
    }
    #freecad_script_execution,
    #agent=coder_assistant,
    #executor=user_proxy,
    #description="Freecad Python console script executor. If execution fails try again with command: '/home/creditizens/freecad_lm-studio/freecadus/AppRun freecadcmd <Python script file>'",
)

# user_proxy execution of function by user_proxy
agent.register_function(
  function_map={
      "freecad_script_execution": freecad_script_execution,
    }
    #freecad_script_execution,
    #agent=user_proxy,
    #executor=user_proxy,
    #description="Freecad Python console script executor. If execution fails try again with command: '/home/creditizens/freecad_lm-studio/freecadus/AppRun freecadcmd <Python script file>'",
)
"""

#### Creation of the Group Chat and his manager (groupechat extras: speaker_selection_method="round_robin", admin_name="coordinator",allow_repeat_speaker=False,)
groupchat = autogen.GroupChat(agents=[coordinator, coder, codechecker], messages=[], max_round=10, speaker_selection_method="auto",allow_repeat_speaker=False, admin_name="coordinator",)
manager = autogen.GroupChatManager(name="manager", groupchat=groupchat, llm_config=llm_config_group_chat,)

coordinator.initiate_chat(
    manager,
    message="""I want a FreeCAD Python script that used only FreeCAD libraries and that creates a 3D cube with bakground contrast and then download the object as 2D image named 'cube_image.png' file at path:'/home/creditizens/freecad_lm-studio/freecadus/cube_image.png'. I am using 'FreeCAD 0.21.2'.
    """,
    model= "gpt-4",
    stream= False,
)

# generate_init_message


