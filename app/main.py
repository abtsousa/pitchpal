# TODO
# Get a simple Python script running
# Add logging and observability
# Get a streaming response going
# Import tools
# Test it out

from phoenix.otel import register
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessageChunk
from tools import get_all_tools
from agent import get_agent

import getpass
import os
import logging
import argparse
import time

# Global variables
APP_NAME = "Tonibot"

# Logging
logging.basicConfig(level=logging.INFO, 
                    format="[%(levelname)s] (%(asctime)s) %(name)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

# Phoenix tracing
def start_phoenix(phoenix_endpoint : str):
    register(
    project_name=APP_NAME,
    auto_instrument=True,
    endpoint=phoenix_endpoint,
    )
    logging.getLogger("openinference").setLevel(logging.CRITICAL)

# QA loop
def qa_loop(agent):
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            #print(f"{APP_NAME}: ", end="", flush=True)

            start_time = time.time()
            
            for message_chunk, metadata in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                stream_mode="messages",
            ):
                if isinstance(message_chunk, AIMessageChunk):
                    print(message_chunk.content, end="", flush=True)
            end_time = time.time()
            print()  # New line after the response
            logger.info(f"Response time: {(end_time - start_time)*1000:.0f} ms")
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

def main():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument(
        "--phoenix-endpoint", 
        help="Phoenix endpoint URL (optional)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Enable logging (critical level if off, info/debug if on)"
    )
    args = parser.parse_args()
    
    # Set logging level based on arguments
    if not args.log:
        logging.getLogger().setLevel(logging.CRITICAL)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    if args.phoenix_endpoint:
        start_phoenix(args.phoenix_endpoint)
    
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    """

    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

    model = ChatOpenAI(model="gpt-4.1-mini-2025-04-14")

    # Use our custom agent
    agent = get_agent(
        model=model,
        tools=get_all_tools(),
        name=APP_NAME,
        prompt=f"You are a helpful football assistant. Today is {datetime.today().strftime('%Y-%m-%d')}. Club World Cup is ongoing, but all the other European events have finished. If the user query does not specify a season, assume it is the latest (2024/25 for European leagues and 2025 for cups). If the user does not specify a league, assume it is the national league for the teams in the query. If any tool fails, figure out the correct parameters (e.g. for team name, 'FCP' should be 'FC Porto') and try again.",
    )

    # Run it
    qa_loop(agent)



if __name__ == "__main__":
    main()
