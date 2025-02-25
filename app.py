from dotenv import load_dotenv
load_dotenv()

import os
AZURE_OPENAI_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_VERSION     = os.getenv("AZURE_OPENAI_VERSION")
AZURE_OPENAI_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY")

AZURE_COGNITIVE_ENDPOINT = os.getenv("AZURE_COGNITIVE_ENDPOINT")
AZURE_COGNITIVE_VERSION  = os.getenv("AZURE_COGNITIVE_VERSION")

GATEKEEPER_ENDPOINT     = os.getenv("GATEKEEPER_ENDPOINT")

from typing import Literal
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from uld_kb import ULDKnowledgeDB
from uld_onerecord import ULD_OneRecord

from datetime import datetime
import chainlit as cl

import base64

import io
import wave
import numpy as np
import tempfile
import logging
from speech_to_text import SpeechToText

import requests
import hashlib

uld_knowkedge_db = ULDKnowledgeDB()
uld_onerecord = ULD_OneRecord(None)

agent = None

@tool
def update_one_record(uld_id: str) -> str:
    """
    Update OneRecord with a new damage record for a specific ULD type.

    Args:
        uld_id (str): The id of the ULD.
    """
    print(f"Updating OneRecord with damage record for ULD {uld_id}")
    uld_onerecord.flag_for_damage(uld_id, damage=True)
    return f"Updated OneRecord with damage record for ULD {uld_id}"

@tool
def get_uld_knowledge(uld_type: Literal["uld_odln_frc", "uld_odln_pallet_net", "uld_odln_pallet", "uld_odln_std_pallet", "uld_odln_std_fabric", "uld_odln_std_solid", "uld_odln_strap"]) -> str:
    """
    Get the knowledge base article to check damages for a specific ULD type.

    Args:
        uld_type (Literal["uld_odln_frc", "uld_odln_pallet_net", "uld_odln_pallet", "uld_odln_std_fabric", "uld_odln_std_solid", "uld_odln_strap"]): The ULD type.
            uld_odln_frc: Operational Damage Limits Notice (ODLN) for Fire Resistant Container
            uld_odln_pallet_net: Operational Damage Limits Notice (ODLN) for Aircraft Pallet Net
            uld_odln_pallet: Operational Damage Limits Notice (ODLN) for Aircraft Pallet
            uld_odln_std_pallet: Operational Damage Limits Notice (ODLN) for Standard Certified Aircraft Pallet (Most common)
            uld_odln_std_fabric: Operational Damage Limits Notice (ODLN) for Standard Certified Aircraft Container (Fabric Door)
            uld_odln_std_solid: Operational Damage Limits Notice (ODLN) for Standard Certified Aircraft Container (Solid Door)
            uld_odln_strap: Operational Damage Limits Notice (ODLN) for Restraint Strap
    """
    return uld_knowkedge_db.get_kb_article(uld_type)

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Use HTTP POST to authenticate the user with remote service
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    url = GATEKEEPER_ENDPOINT+"/authenticate"
    payload = {"login": username, "password": hashed_password}
    print(payload)
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("authenticated"):
            uld_onerecord.access_token = result.get("one_record_token")
            return cl.User(identifier=username, metadata={"role": result.get("role", "user"), "provider": "credentials"})
    except Exception as e:
        logging.error(f"Authentication error: {e}")
    return None

@cl.on_chat_start
async def on_chat_start():
    global agent
    tools = [get_uld_knowledge, update_one_record]
    model = AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        openai_api_version=AZURE_OPENAI_VERSION,
        api_key=AZURE_OPENAI_API_KEY
        )
    memory = MemorySaver()
    agent = create_react_agent(model, tools, checkpointer=memory)
    agent.debug = False

@cl.on_message
async def on_message(msg: cl.Message):
    config = {"configurable": {"thread_id": cl.context.session.id}}
    cb = cl.LangchainCallbackHandler()
    final_answer = cl.Message(content="")

    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_message = SystemMessage(content=f"""You are an Air Cargo AI Assistant designed to help users asses ULD air worthiness. The current date and time is {date_time}.""")

    if not msg.elements: # if no picture was uploaded
        messages = [system_message, HumanMessage(content=msg.content)]
    else: # pass pictures as base64 encoded images
        content = [{"type": "text", "text": msg.content}]
        for element in msg.elements:
            if element.mime == "image":
                with open(element.path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                    content.append({"type": "image_url", "image_url": {"url": f"data:image;base64,{base64_image}"}})
        messages = [system_message, HumanMessage(content=content)]

    for msg, metadata in agent.stream({"messages": messages}, stream_mode="messages", config=RunnableConfig(callbacks=[cb], **config)):
        if msg.content and isinstance(msg, AIMessage):
            await final_answer.stream_token(msg.content)

    await final_answer.send()

# -------------------------
# Audio handling capabilities:
async def speech_to_text_tool(audio_file):
    stt = SpeechToText(
            url = AZURE_COGNITIVE_ENDPOINT,
            version = AZURE_COGNITIVE_VERSION,
            key = AZURE_OPENAI_API_KEY
        )
    return stt.transcribe(audio_file)

@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("audio_chunks", [])
    logging.info("Audio recording started")
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    logging.info("Audio chunk received")
    audio_chunks = cl.user_session.get("audio_chunks")
    if audio_chunks is not None:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)
        logging.debug("Audio chunk received and appended")

@cl.on_audio_end
async def on_audio_end():
    logging.info("Audio recording ended, processing audio")
    await process_audio()

async def process_audio():
    if audio_chunks := cl.user_session.get("audio_chunks"):
        concatenated = np.concatenate(list(audio_chunks))
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)           # mono
            wav_file.setsampwidth(2)           # 16-bit
            wav_file.setframerate(24000)       # 24kHz
            wav_file.writeframes(concatenated.tobytes())
        wav_buffer.seek(0)
        cl.user_session.set("audio_chunks", [])
        logging.info("Audio chunks concatenated into wav_buffer")
    else:
        logging.warning("No audio chunks found; aborting processing")
        return

    with wave.open(wav_buffer, 'rb') as wav_reader:
        frames = wav_reader.getnframes()
        rate = wav_reader.getframerate()
        duration = frames / float(rate)
    logging.info(f"Audio duration: {duration:.2f} seconds")
    if duration <= 2:
        logging.warning("The audio is too short, please try again.")
        return

    audio_buffer = wav_buffer.getvalue()
    input_audio_el = cl.Audio(content=audio_buffer, mime="audio/wav")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_buffer)
        temp_filepath = temp_audio.name

    transcription = await speech_to_text_tool(temp_filepath)
    os.unlink(temp_filepath)
    
    # New: Display transcribed text as a user message in the chat UI.
    await cl.Message(content=transcription['text'],type="user_message").send()

    # Then send the transcribed text to the agent for processing:
    config = {"configurable": {"thread_id": cl.context.session.id}}
    cb = cl.LangchainCallbackHandler()
    final_agent_msg = cl.Message(content="")

    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_message = SystemMessage(
        content=f"""You are an Air Cargo AI Assistant designed to help users asses ULD air worthiness.
If you find a ULD to be damaged, ask the user if he want to update OneRecord with the damage record.
The current date and time is {date_time}."""
    )
    human_message = HumanMessage(content=transcription['text'])
    for msg, metadata in agent.stream(
        {"messages": [system_message, human_message]}, 
        stream_mode="messages", 
        config=RunnableConfig(callbacks=[cb], **config)
    ):
        if msg.content and isinstance(msg, AIMessage):
            await final_agent_msg.stream_token(msg.content)
    await final_agent_msg.send()
