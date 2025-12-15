LLM Knowledge Engine Basic API-DeepSeek OpenAI API is compatible with OpenAI's API specification.You only need to replace base_url and api_key with relevant configurations, without requiring any additional modifications to your application, to seamlessly switch your application to the corresponding large model.
base_url:https://api.lkeap.tencentcloud.com/v1
api_key: Create it on the console API KEY webpage. For operation steps, see Quick Start.
API request address full path: https://api.lkeap.tencentcloud.com/v1/chat/completions
Call conditions can be viewed in Console > Data Report. For billing details, refer to Billing Overview.
Online Experience
If you want to experience DeepSeek model dialogue directly on a web page, we recommend you go to Tencent Cloud Intelligence development platform to create a dialogue application.
Supported Models
DeepSeek R1 Model
Model
Parameter Quantity
Maximum Context Length
Maximum Input Length
Maximum Output Length
DeepSeek-R1
671B
48k
16k
32k
DeepSeek-R1-0528
671B
48k
16k
32k
DeepSeek V3 Model
Model
Parameter Quantity
Maximum Context Length
Maximum Input Length
Maximum Output Length
DeepSeek-V3
671B
48k
16k
32k
DeepSeek V3.1-Terminus Model
Model
Parameter Quantity
Maximum Context Length
Maximum Input Length
Maximum Output Length
DeepSeek-V3.1-Terminus
685B
128k
96k
32k
DeepSeek - R1 (Model Parameter Value: deepseek-r1)
DeepSeek-R1 is a 671B model trained with reinforcement learning. Its inference process involves extensive reflection and verification, with thought chains reaching tens of thousands of words. This series of models delivers excellent inference effectiveness in math, code, and various complex logical reasoning tasks, displaying the complete thinking process for users.
DeepSeek-R1-0528 (Model Parameter Value Is DeepSeek-R1-0528)
DeepSeek-R1-0528 is a 671B model. With architecture optimization and policy upgrade, it shows significant improvement in code generation, long text processing, and complex reasoning compared to the previous version.
Using DeepSeek-V3 (Model Parameter Value: deepseek-v3)
DeepSeek-V3 is the latest version released on 0324. DeepSeek-V3 is a 671B parameter MoE model, with strong advantages in tasks such as encyclopedia knowledge and math reasoning.
DeepSeek-V3.1-Terminus (Model Parameter Value Is Deepseek-V3.1-Terminus)
DeepSeek-V3.1-Terminus is a 685B-parameter MoE model. While preserving the model's original capabilities, it has optimized linguistic consistency and Agent capabilities, making the output performance more stable compared to the previous version.
Quick Start
Prerequisites for using the API: LLM Knowledge Engine Basic API has been enabled and an API Key has been created in the API Key Management section of the Tencent Cloud console.
If you are using LLM Knowledge Engine Basic API for the first time, refer to the Quick Start to enable LLM Knowledge Engine Basic API and modify the model parameter in the example code to the model name you need to call from the table above.
Since the thinking process of the deepseek-r1 model may take a longer time, possibly causing slow response or timeout, we recommend you prioritize using the streaming output method for calls.
Installing the SDK
Make sure Python 3.8 or later is installed.
Install or update the OpenAI Python SDK
Run the following command:
pip install -U openai
If execution fails, change pip to pip3.
Sample Code Snippet
Non-Streaming Request
Python
cURL
﻿
import os
from openai import OpenAI
﻿
client = OpenAI(
    api_key="LKEAP_API_KEY",
    base_url="https://api.lkeap.tencentcloud.com/v1",
)
﻿
completion = client.chat.completions.create(
    model="deepseek-r1",  
    messages=[
        {'role': 'user', 'content': 'Which is greater, 9.9 or 9.11?'}
        ]
)
﻿
print("reasoning_content:")
print(completion.choices[0].message.reasoning_content)
print("content:")
print(completion.choices[0].message.content)
Multi-Round Dialogue
LLM Knowledge Engine Basic API does not record your historical conversation information by default. The multi-round dialogue feature enables the large model to "have memory," meeting requirements for continuous communication such as follow-up questions and information collection. If you use the deepseek-r1 model, you will receive the reasoning_content field (thinking process) and the content field (reply content). You can add the content field to the context using {'role': 'assistant', 'content': API returned content}, with no need to add the reasoning_content field.
Python
cURL
import os
from openai import OpenAI
client = OpenAI(
    api_key="LKEAP_API_KEY",
    base_url="https://api.lkeap.tencentcloud.com/v1",
)
﻿
messages = [
    {'role': 'user', 'content': 'hello'},
    {'role': 'assistant', 'content': 'hi, how can I assist you?'},
    {'role': 'user', 'content': 'Which is greater, 9.9 or 9.11?'}
]
﻿
completion = client.chat.completions.create(
    model="deepseek-r1",  
    messages=messages
)
﻿
print("="*20+"first-round dialogue"+"="*20)
print("="*20+"reasoning_content"+"="*20)
print(completion.choices[0].message.reasoning_content)
print("="*20+"content"+"="*20)
print(completion.choices[0].message.content)
﻿
messages.append({'role': 'assistant', 'content': completion.choices[0].message.content})
messages.append({'role': 'user', 'content': 'who are you'})
print("="*20+"second-round dialogue"+"="*20)
completion = client.chat.completions.create(
    model="deepseek-r1",
    messages=messages
)
print("="*20+"reasoning_content"+"="*20)
print(completion.choices[0].message.reasoning_content)
print("="*20+"content"+"="*20)
print(completion.choices[0].message.content)
Streaming Output
The deepseek-r1 model may output a relatively long thinking process. To reduce timeout risk, recommend you use the streaming output method to call the deepseek-r1 model.
Python
cURL
from openai import OpenAI
import os
﻿
client = OpenAI(
    api_key="LKEAP_API_KEY",
    base_url="https://api.lkeap.tencentcloud.com/v1",
)
﻿
def main():
    reasoning_content = ""
    answer_content = ""     
    is_answering = False
    
    # Create chat completion request
    stream = client.chat.completions.create(
        model="deepseek-r1",  
        messages=[
            {"role": "user", "content": "Which is greater, 9.9 or 9.11?"}
        ],
        stream=True
    )
﻿
    print("\n" + "=" * 20 + "reasoning processes" + "=" * 20 + "\n")
﻿
    for chunk in stream:
        # Process Usage Information
        if not getattr(chunk, 'choices', None):
            print("\n" + "=" * 20 + "Token usage" + "=" * 20 + "\n")
            print(chunk.usage)
            continue
﻿
        delta = chunk.choices[0].delta
﻿
        if not getattr(delta, 'reasoning_content', None) and not getattr(delta, 'content', None):
            continue
﻿
        if not getattr(delta, 'reasoning_content', None) and not is_answering:
            print("\n" + "=" * 20 + "reasoning_content" + "=" * 20 + "\n")
            is_answering = True
﻿
        if getattr(delta, 'reasoning_content', None):
            print(delta.reasoning_content, end='', flush=True)
            reasoning_content += delta.reasoning_content
        elif getattr(delta, 'content', None):
            print(delta.content, end='', flush=True)
            answer_content += delta.content
﻿
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"error:{e}")
        
Function Calling
DeepSeek-V3 now supports function calling. The calling process is as follows (taking retrieving local weather as an example):
﻿
Operation Guide
Function Calling refers to the model's capability to invoke external functions or APIs to retrieve information or interact with external systems when responding to user queries.
Function Calling user guide (use fetching local temperature as an example):
Define the function get_weather.
First request to the chat API: Send the user's question and function definitions (name, description, parameters). The model will select the appropriate function and fills its parameters.
First response from the model: Client-side executes the function  to obtain results (the model only specifies the function and parameters; actual function execution is handled by the client's code).
Second request to the chat API: Append the first response and function call results to the conversation context based on the first request, then resubmit the request.
Second response from the model: The model generates the final answer.
First request example:
﻿
```python
curl --location 'https://api.lkeap.tencentcloud.com/v1/chat/completions' \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $API_KEY" \
--data '{
  "model": "deepseek-v3",
  "messages": [
        {
            "role": "user",
            "content": "What's the weather like in Paris today?"
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current temperature for provided coordinates in celsius.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number"
                        },
                        "longitude": {
                            "type": "number"
                        }
﻿
                    },
                    "required": [
                        "latitude","longitude"
                    ]
                }
            }
        }
    ]
}'
```
﻿
First response example:
﻿
JSON
﻿
```json
{
  "id": "cabe32d2b30dd30ac3d7aad02f235dd4",
  "choices": [
    {
      "finish_reason": "tool_calls",
      "index": 0,
      "message": {
        "content": "Call the weather query tool (get_weather) to get the weather info in Paris.\n\t\n\tThe user wants to know today's weather in Paris. I need to call the weather query tool (get_weather) to get the weather info in Paris."
        "role": "assistant",
        "tool_calls": [
          {
            "id": "call_cvdrgkk2c3mceb26d7sg",
            "function": {
              "arguments": "{\"latitude\":48.8566,\"longitude\":2.3522}",
              "name": "get_weather"
            },
            "type": "function",
            "index": 0
          }
        ]
      }
    }
  ],
  "created": 1742452818,
  "model": "hunyuan-turbos-latest",
  "object": "chat.completion",
  "system_fingerprint": "",
  "usage": {
    "completion_tokens": 48,
    "prompt_tokens": 22,
    "total_tokens": 70
  }
}
```
﻿
Second request example:
﻿
```python
curl --location 'https://api.lkeap.tencentcloud.com/v1/chat/completions' \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $API_KEY" \
--data '{
  "model": "deepseek-v3",
  "messages": [
        {
            "role": "user",
            "content": "What's the weather like in Paris today?"
        },
        {
            "role": "assistant",
            "content": "Call the weather query tool (get_weather) to get the weather info in Paris.\n\t\n\tThe user wants to know today's weather in Paris. I need to call the weather query tool (get_weather) to get the weather info in Paris."
            "tool_calls": [
                {
                    "id": "call_cvdu67s2c3mafqgr1g6g",
                    "function": {
                    "arguments": "{\"latitude\":48.8566,\"longitude\":2.3522}",
                    "name": "get_weather"
                    },
                    "type": "function",
                    "index": 0
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_cvdu67s2c3mafqgr1g6g",
            "content": "11.7"
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current temperature for provided coordinates in celsius.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number"
                        },
                        "longitude": {
                            "type": "number"
                        }
﻿
                    },
                    "required": [
                        "latitude","longitude"
                    ]
                }
            }
        }
    ]
}'
```
﻿
Second response example:
﻿
JSON
﻿
```json
{
  "id": "b03283653e27bc78a9c095699cfbc123",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "The current temperature in Paris is 7.6°C.",
        "role": "assistant"
      }
    }
  ],
  "created": 1742453367,
  "model": "hunyuan-turbos-latest",
  "object": "chat.completion",
  "system_fingerprint": "",
  "usage": {
    "completion_tokens": 24,
    "prompt_tokens": 71,
    "total_tokens": 95
  },
  "note": "The above content is AI generation and does not mean the developer's standpoint. Do not delete or modify this tag."
}
```
﻿
Continue the dialogue afterward.
Note:
Under OpenApi compatible format calling method, only V3 series models support Function Calling , while R1 models do not currently support it.
Deep Thinking
Enable deep thinking by calling the deepseek-r1 model (the thinking process returns via reasoning_content).
Note
Stability
If the response "concurrency exceeded" occurs after execution, it indicates your request encountered traffic throttling. This is usually due to temporarily insufficient server resources. We recommend trying again later, as the server workload may have been mitigated by then.
DeepSeek-R1
Unsupported parameter set and features
Function Calling,JSON Output,Continue dialogue prefix,Context hard disk cache.
Unsupported parameters
presence_penalty,frequency_penalty,logprobs,top_logprobs.
Supported parameters
top_p,temperature,max_tokens.
Parameter default value:
temperature: 0.6 (value ranges from 0 to 2)
top_p: 0.6 (value ranges from 0 to 1]
Do not set System Prompt (comes from official documentation).
DeepSeek-V3
Unsupported parameter set and features
JSON Output,Continue dialogue prefix,Context hard disk cache.
Unsupported parameters
presence_penalty,frequency_penalty,logprobs,top_logprobs.
Supported parameters and features
top_p, temperature, max_tokens parameters.
Function Calling feature
support tools parameter
support tool_choice parameter (supports auto, none, Forced Function (required feature unsupported))
Parameter default value:
temperature: 0.6 (value ranges from 0 to 2)
top_p: 0.6 (value ranges from 0 to 1]
DeepSeek-V3.1-Terminus
Unsupported parameter set and features
Function Calling, Dialogue Prefix Continuation, Context Hard Disk Cache.
Unsupported parameters
logprobs,top_logprobs.
Supported parameters and features
top_p,temperature,max_tokens,presence_penalty,frequency_penalty.
JSON Output feature
Support json_object mode.
Parameter default value
temperature: 0.6 (value ranges from 0 to 2)
top_p: 0.6 (value ranges from 0 to 1)
Stay tuned for follow-up updates.
Error Code
Error Code
Error Message
Description
20031
not enough quota
Your account currently has no available resources. To continue to use, please toggle on the postpaid switch in postpaid settings or go to the purchase page to purchase a prepaid concurrency package.
20034
concurrency exceeded
Your request encountered traffic throttling. This is usually due to temporarily insufficient server resources. We recommend trying again later, as the server load may have been mitigated by then.
20059
input content too long
Input length exceeds context length. Reduce input content length.
Incorrect Example
{"error":{"message":"not enough quota","type":"runtime_error","param":null,"code":"20031"}}
﻿