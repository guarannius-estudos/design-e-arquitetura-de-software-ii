import azure.functions as func
import logging

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_transportadora(timer: func.TimerRequest) -> None:
    """
    Trigger de extração agendada (diária às 06:00 UTC).
    Apenas delega para o orchestrator — sem lógica de negócio aqui.
    """
    logging.info("extract_transportadora iniciado.")
    logging.info("extract_transportadora finalizado.")