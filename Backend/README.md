# The-Secure-AI-Medical-Assistant
Build a conversational AI assistant for a simulated medical practice. The assistant's primary goal is to be helpful, booking appointments and answering questions while its absolute, unbreakable rule is to protect patient privacy.

cd <Backend>

python -m venv venv

venv\Scripts\activate
//Attivando l’ambiente virtuale con `venv\Scripts\activate`, tutte le librerie che installerò o utilizzerò saranno **contenute all’interno della cartella `venv`** e non influenzeranno le librerie Python globali del sistema.

pip install -r requirements.txt     
//scarica tutte le dipendenze del progetto dentro alla cartella venv

L’ambiente virtuale è fondamentale perché permette di usare Python e le librerie specifiche del progetto contenute nella cartella venv.

Se non lo attivassimo:

Python userebbe le librerie globali del sistema

Qualsiasi pacchetto installato verrebbe aggiunto globalmente, rischiando conflitti con altri progetti che potrebbero richiedere librerie diverse o versioni differenti

Attivando il venv, invece, tutte le librerie rimangono isolate nel progetto, un po’ come i node_modules di Node.js: ogni progetto ha le proprie dipendenze locali e non interferisce con gli altri.