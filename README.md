# The-Secure-AI-Medical-Assistant

# Avvio app web
Per avviare l’applicazione web, entra nella cartella Frontend, eseguire prima "npm install" per installare tutte le dipendenze, quindi avvia il server di sviluppo con: "npm run dev". l'app web sarà disponibile all'indirizzo "http://localhost:5173/"


# Server backend
Per lo sviluppo del backend è previsto l’utilizzo di un ambiente virtuale Python. L’ambiente viene creato tramite il comando "py -3.14 -m venv .venv" e attivato con ".\.venv\Scripts\activate". L’uso di un ambiente virtuale è fondamentale, poiché consente di isolare completamente le dipendenze del progetto dalle librerie Python globali del sistema, evitando conflitti e garantendo riproducibilità. Una volta attivato l’ambiente, tutte le dipendenze necessarie vengono installate tramite il comando "pip install -r requirements.txt".

Il server backend può essere avviato localmente utilizzando "uvicorn main:app --reload"; tuttavia, per il normale utilizzo e per il testing dell’applicazione web, non è necessario avviare il backend in locale. Il backend è infatti già distribuito online all’indirizzo "https://the-secure-ai-medical-assistant.onrender.com" ed è stato intenzionalmente deployato per consentire agli agenti IA remoti di LettaAI di accedere alle API tramite tool protetti. Allo stesso modo, il database MongoDB è ospitato su un cluster cloud MongoDB Atlas ed è già operativo. 
Le chiamate api non funzioneranno nel caso di avvio locale. Ho usato il locale solo durante la prima fase del progetto in cui generavo gli agenti e testavo le funzioni di autenticazione.

# Framework LettaIA
Per la gestione degli agenti IA ho scelto di utilizzare il framework LettaAI.
Il framework consente tre modalità di utilizzo: chiamate API dirette, SDK oppure ADE (Agent Development Environment). In questo progetto ho scelto l’SDK, che permette di creare e configurare agenti e tool interamente da codice, senza interventi manuali sull’ADE.

L’ADE è stato utilizzato esclusivamente a scopo di debug, mentre in esecuzione normale tutti gli agenti e i tool vengono gestiti e creati dinamicamente dal backend tramite SDK, garantendo maggiore controllo, automazione e sicurezza.

La documentazione che ho seguito per usare la sdk è:
"https://docs.letta.com/api/python"
SPiegazione codice sdk per utilizzare agenti e tool:
# 1
Crea il client LettaAI utilizzando le credenziali del progetto. Questo client è il punto di accesso per creare agenti, tool e blocchi di contesto tramite l’SDK. (le key di Letta mi sono state fornite da LettaIA una volta che mi sono registrato sul sito)

client = Letta(
    api_key=os.getenv("LETTA_API_KEY"),
    project_id=os.getenv("LETTA_PROJECT_ID")
)
# 2
Trasforma una funzione Python in un tool invocabile dall’agente IA.
Il tool viene creato (o aggiornato) globalmente sul server di LettaAI e può essere registrato anche una sola volta. Successivamente, i tool già registrati vengono semplicemente associati agli agenti al momento della loro creazione.

Il metodo upsert_from_function garantisce che, se il tool esiste già ed è identico, non venga modificato; se invece la funzione è stata aggiornata nel codice, il tool esistente viene sovrascritto con la nuova versione, mantenendo il sistema sempre allineato all’implementazione più recente.
Ogni funzione esposta come tool deve includere una docstring chiara che descriva cosa fa e in quali casi deve essere utilizzata, così da permettere all’agente IA di capire correttamente quando invocarla e con quale scopo.

add_appointment_tool = client.tools.upsert_from_function(
            func=add_appointment,
            timeout=60
        )

# 3
Definisce il ruolo dell’agente, specificandone il compito principale (assistente per la gestione degli appuntamenti medici). Questo blocco fa parte del contesto permanente dell’agente e viene letto ad ogni messaggio, guidando in modo coerente il comportamento del modello. È impostato come read-only per renderlo immutabile, impedendo sia all’agente sia a eventuali input malevoli di modificarlo o indurlo a cambiare ruolo.
role_block = client.blocks.create(
        label="role",
        value="Sei un assistente per la gestione di appuntamenti medici.",
        read_only=True,
    )

# 4
Viene creato un agente IA dedicato a ciascun utente, configurato con:
Model: il modello LLM utilizzato dall’agente.
Block IDs: blocchi di contesto read-only che definiscono ruolo, istruzioni operative, policy di sicurezza e informazioni dell’utente.
Secrets: variabili d’ambiente sensibili (user_id, email, token di accesso), invisibili e non modificabili dall’agente.
Tools: insieme di tool autorizzati che l’agente può utilizzare per interagire con il backend in modo controllato.
Una volta creato, l’agente risiede persistentemente sui server LettaAI. Per questo motivo, il codice di gestione dell’agente deve essere sempre presente:
se l’utente è nuovo, viene creato un nuovo agente dedicato;
se l’utente esiste già, il sistema recupera l’agente precedentemente associato e lo riutilizza.

agent = client.agents.create(
        name=f"assistant_user_{user_id}",
        model="openai/gpt-4o-mini",
        block_ids=[
            role_block.id,
            instructions_block.id,
            security_policy_block.id,
            user_info_block.id
        ],
        secrets={
            "LETTA_TOOL_TOKEN": os.getenv("LETTA_TOOL_TOKEN"),
            "USER_ID": user_id,
            "EMAIL": email
        },
        tools=[t.name for t in [add_appointment_tool, get_slots_tool, get_user_appointments_tool, delete_appointment_tool, update_appointment_tool] if t]
    )

# 5
Qua recupero l'id dell'agente
agent_id = get_or_create_agent(user_id, email)

# 6
Invia un messaggio dell’utente all’agente IA specificato e ne avvia l’elaborazione.
In particolare:
    identifica l’agente tramite agent_id;
    aggiunge il messaggio alla conversazione con ruolo user;
    permette all’agente di leggere il proprio contesto (blocchi, memoria, policy);
    consente all’agente di decidere se rispondere direttamente o invocare uno o più tool;
    attende la risposta finale dell’agente (fino a timeout secondi).
response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": message}],
            timeout=120
        )

# Struttura cartelle
contenuto nei file python:
appointment_routes.py – API che gli agenti IA chiamano tramite tool per gestire appuntamenti.

auth_routes.py – API di registrazione, login e logout.

frontend_routes.py – API per il frontend, per visualizzare messaggi e appuntamenti dell’utente.

letta_routes.py – API che passa i messaggi dell’utente agli agenti IA e restituisce le risposte.

mfa_routes.py – Gestisce l’autenticazione a più fattori (MFA) con FIDO2/WebAuthn: registrazione e autenticazione di chiavi sicure.

auth.py – Funzioni di utilità per decodifica e verifica dei token JWT.

fido.py – Inizializza il server FIDO2/WebAuthn per MFA.

agent_service – Gestisce la creazione e l’utilizzo di agenti IA LettaIA per ogni utente, registrando i tool e inoltrando i messaggi all’agente per la gestione sicura degli appuntamenti.

main.py – Inizializza il server FastAPI e collega tutti i router alle rispettive route.

Per quanto riguarda le librerie fido2 e webAuthn ho seguito la documentazione:
"https://developers.yubico.com/python-fido2/API_Documentation/autoapi/fido2/"

Per l'mfa uso 4 chiamate api principali che utilizzano 4 metodi fondamentali:
register_begin – Il server genera una sfida crittografica per la registrazione di una nuova chiave MFA e la invia al browser. Tramite WebAuthn, il browser crea localmente una coppia di chiavi (privata e pubblica), mantenendo la chiave privata sul dispositivo dell’utente.

register_complete – Il server riceve la chiave pubblica e la firma associata, ne verifica la validità e registra nel database la chiave pubblica insieme al relativo identificativo, associandoli all’utente.

authenticate_begin – Durante un login successivo, dopo la verifica di username e password, il server genera una nuova sfida temporanea e la invia al browser.

authenticate_complete – Il browser firma la sfida utilizzando la chiave privata e invia la risposta al server, che ne verifica la correttezza. L’accesso viene concesso solo se la verifica ha esito positivo.
