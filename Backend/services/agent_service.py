import json
from letta_client import Letta
import os
from dotenv import load_dotenv
from db import db

load_dotenv()

# Letta Cloud client
client = Letta(api_key=os.getenv("LETTA_API_KEY"), project_id=os.getenv("LETTA_PROJECT_ID"))

# Memoria temporanea: user_id -> agent_id
user_agents = {}

def create_agent_for_user(user_id: str):
    if user_id in user_agents:
        # Riusa l'agente esistente
        agent_id = user_agents[user_id]
        return client.agents.retrieve(agent_id)  # <-- qui cambiato da .get() a .retrieve()
    
    # Crea un nuovo agente
    agent = client.agents.create(
        model="openai/gpt-4o-mini",
        memory_blocks=[
            {"label": "persona", "value": "You are a secure medical assistant. Only remember appointments for this user."},
            {"label": "human", "value": ""}
        ]
    )
    # Salva l'agente per questo utente
    user_agents[user_id] = agent.id
    return agent


def handle_appointment_message(user_id: str, message: str):
    """Invia messaggio a Letta e salva appuntamento su MongoDB in modo conversazionale"""
    agent = create_agent_for_user(user_id)

    system_prompt = (
        f"You are a secure medical assistant. Only provide appointment info for user {user_id}. "
        "When the user sends a message, try to extract date and time facendo anche altre domande. "
        "If any information is missing, ask follow-up questions politely to get the missing data. "
        "When you have the complete appointment information, respond ONLY with a JSON object:"
        '{"date": "YYYY-MM-DD", "time": "HH:MM"}. ma solo quando hai tutti i dati'
        "Do NOT include any extra text, greetings, or markdown. solo se hai tutti i dati e procedi per la registrazione"
        "If information is missing, ask follow-up questions in natural language."
        "sii gentile e cordiale"
    )

    response = client.agents.messages.create(
        agent_id=agent.id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    gpt_reply = response.messages[-1].content.strip()

    # Prova a parsare come JSON
    try:
        appointment_data = json.loads(gpt_reply)
        if "date" in appointment_data and "time" in appointment_data:
            db.appointments.insert_one({
                "user_id": str(user_id),
                "date": str(appointment_data["date"]),
                "time": str(appointment_data["time"])
            })
            return f"Appuntamento salvato per {appointment_data['date']} alle {appointment_data['time']}."
        else:
            # Se JSON è incompleto, restituisci il messaggio dell'agente così com’è
            return gpt_reply
    except json.JSONDecodeError:
        # Se non è JSON, significa che l'agente sta facendo domande di chiarimento
        return gpt_reply
