import os
from openrouter import OpenRouter
import ai_manager

def send_request(input_text="What is a tree in one sentence?"):
  with OpenRouter(
      api_key=os.getenv("OPENROUTER_API_KEY", ""),
  ) as open_router:
      res = open_router.chat.send(
          model= "dots-studio/dots-3-note-preview:free",
          messages=[
              {"content": input_text, "role": "user"}
          ],
        #   response_format={
        #      "type" : "json_schema",
        #      "json_schema": {
        #         "type": "object",
        #         "properties":{
        #            "confidence level": {
        #               "type": "number",
        #               "description": "How correct is the reply"
        #            },
        #            "message": {
        #               "type": "string",
        #               "description": "Reply"
        #            }
        #         }
        #      }
        #   },
          stream=False,
      )
      # print(res.choices[0].message.content)
      print(res)
      content_str = ai_manager.receive_response(res)
      print('\n\n')
      print(content_str)
      return res

send_request()