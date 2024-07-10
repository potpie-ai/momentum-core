import logging
import os

from server.key_management.secret_manager import get_secret
from server.utils.firestore_helper import FirestoreHelper
from langchain_openai.chat_models import ChatOpenAI
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
import asyncio 

color_prefix_by_role = {
    "system": "\033[0m",  # gray
    "human": "\033[0m",  # gray
    "user": "\033[0m",  # gray
    "ai": "\033[92m",  # green
    "assistant": "\033[92m",  # green
}


def get_llm_client(user_id, model_name):
    provider_key = get_provider_key(user_id)
    return create_client(provider_key["provider"], provider_key["key"], model_name, user_id)

def create_client(provider, key, model_name, user_id):
    if provider == "openai":
        PORTKEY_API_KEY = os.environ.get("PORTKEY_API_KEY")
        PROVIDER_API_KEY = key

        portkey_headers = createHeaders(api_key=PORTKEY_API_KEY,provider="openai", metadata={"_user":user_id, "environment":os.environ.get("ENV")})

        return ChatOpenAI(api_key=PROVIDER_API_KEY, model=model_name, base_url=PORTKEY_GATEWAY_URL, default_headers=portkey_headers)
        

def get_provider_key(customer_id):
    firestore_helper = FirestoreHelper()
    preference = firestore_helper.get(customer_id, "preferences").get()
    if preference.exists and preference.get("provider") == "openai":
        return {
            "provider": "openai",
            "key": get_secret("openai", customer_id)["api_key"],
        }
    else:
        return {"provider": "openai", "key": os.environ.get("OPENAI_API_KEY")}


async def llm_call(client, messages, print_text=True, temperature=0.4):
    response = await asyncio.to_thread(client, messages=messages, temperature=temperature)
    if print_text:
        print_message_delta(response)
    return response


def print_messages(
    messages, color_prefix_by_role=color_prefix_by_role
) -> None:
    """Prints messages sent to or from GPT."""
    for message in messages:
        role = message.type
        content = message.content
        logging.info(f"[{role}]\n{content}")


def print_message_delta(
    delta, color_prefix_by_role=color_prefix_by_role
) -> None:
    """Prints a chunk of messages streamed back from GPT."""
    role = delta.type
    logging.info(f"[{role}]\n")
    content = delta.content
    logging.info(content)


def print_message_delta_openai(
    delta, color_prefix_by_role=color_prefix_by_role
) -> None:
    """Prints a chunk of messages streamed back from GPT."""
    role = delta.role
    logging.info(f"[{role}]\n")
    content = delta.content
    logging.info(content)
