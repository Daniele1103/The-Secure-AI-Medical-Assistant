# The-Secure-AI-Medical-Assistant
Build a conversational AI assistant for a simulated medical practice. The assistant's primary goal is to be helpful, booking appointments and answering questions while its absolute, unbreakable rule is to protect patient privacy.

cd <Backend>

py -3.14 -m venv .venv
//creo un ambiente python di cui userò il python dentro alla cartella e tutte le dipendenze entreranno li, sarà il mio ambiente

.\.venv\Scripts\activate
//Attivando l’ambiente virtuale con `venv\Scripts\activate`, tutte le librerie che installerò o utilizzerò saranno **contenute all’interno della cartella `venv`** e non influenzeranno le librerie Python globali del sistema.

pip install -r requirements.txt     
//scarica tutte le dipendenze del progetto dentro alla cartella venv (perchè sono dentro l'ambiente, se non l'avessi fatto me le installerebbe globalmente)

L’ambiente virtuale è fondamentale perché permette di usare Python e le librerie specifiche del progetto contenute nella cartella venv.

Se non lo attivassimo:

Python userebbe le librerie globali del sistema

Qualsiasi pacchetto installato verrebbe aggiunto globalmente, rischiando conflitti con altri progetti che potrebbero richiedere librerie diverse o versioni differenti

Attivando il venv, invece, tutte le librerie rimangono isolate nel progetto, un po’ come i node_modules di Node.js: ogni progetto ha le proprie dipendenze locali e non interferisce con gli altri.





Implementazione autenticazione:
quando faccio l'accesso, il backend crea un token jwt e LUI IL SERVER lo salva nel browser del client che lo ha richiesto, in questo modo il token è al sicuro da qualsiasi tipo di attacco XSS in quanto il client non potrà mai accedervi.
Per ritornare il payload del token oppure per rimuoverlo al momento del logout, il client fa richiesta al server e ci pensa lui. inoltre a queso punto per ogni richiesta in cui viene richiesto il token, il client non dovrà passarlo ma sarà passato in automatico nella richiesta http.{ withCredentials: true }


Il server invia il token come cookie nella risposta HTTP.

Il browser riceve il cookie e lo salva automaticamente per quel dominio.

Grazie a HttpOnly, JavaScript nel browser non può leggere il cookie, quindi il token non può essere rubato facilmente via XSS.

Ad ogni richiesta futura verso lo stesso dominio, il browser invia il cookie automaticamente al server, senza che il client debba fare nulla.