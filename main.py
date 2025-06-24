# TODO
# Get a simple Python script running
# Add logging and observability
# Get a streaming response going
# Import tools
# Test it out

from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessageChunk

import getpass
import os
# Global variables
APP_NAME = "Tonibot"


# QA loop
def qa_loop(agent):
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            #print(f"{APP_NAME}: ", end="", flush=True)
            
            for message_chunk, metadata in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                stream_mode="messages",
            ):
                if isinstance(message_chunk, AIMessageChunk):
                    print(message_chunk.content, end="", flush=True)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

def main():
    if not os.environ.get("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

    # TODO switch to our custom agent, this is just to get an input-output loop going
    agent = create_react_agent(
        model=model,
        name=APP_NAME,
        prompt=f"You are a helpful football assistant. Today is {datetime.today().strftime('%Y-%m-%d')}. If the user query does not specify a season, assume it is 2024 for European leagues and 2025 for cups. If the user does not specify a league, assume it is the national league for the teams in the query. If any tool fails, figure out the correct parameters (e.g. for team name, 'FCP' should be 'FC Porto') and try again.",
        tools=[],
    )

    # Run it
    qa_loop(agent)



if __name__ == "__main__":
    main()
