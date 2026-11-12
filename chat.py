"""Terminal chat with the NL→SQL agent. Every SELECT waits for your approval."""
import asyncio
from pathlib import Path

from google import genai
from mcp import Client

from nl_sql_agent.agent import run_turn
from nl_sql_agent.chart import can_plot, save_bar_chart
from nl_sql_agent.client import server_parameters
from nl_sql_agent.config import get_api_key, get_model_name
from nl_sql_agent.tool_policy import load_pins, verify_tools
from nl_sql_agent.tracing import TraceLog

CHART_PATH = Path("charts/last.png")


def confirm(sql: str) -> bool:
    print("\n--- Query proposta ---------------------------")
    print(sql)
    print("----------------------------------------------")
    return input("Eseguo? [s/N] ").strip().lower() == "s"

async def main() -> None:
    llm = genai.Client(api_key=get_api_key())
    model = get_model_name()
    trace =  TraceLog(Path("logs/traces.jsonl"), echo=True)
    history, last_result = [], None
    
    async with Client(server_parameters()) as mcp_client:
        tools = (await mcp_client.list_tools()).tools
        verify_tools(tools, load_pins())
        print(f"Modello: {model}. Tool verificati: {[t.name for t in tools]}")
        print("Comandi: /grafico salva il grafico dell'ultimo risultato, /esci chiude.")
        
        while True:
            text = (await asyncio.to_thread(input, "\nTu: ")).strip()
            if text in ("/esci", "exit"):
                break
            if text == "/grafico":
                if can_plot(last_result):
                    print(f"Grafico salvato in {save_bar_chart(last_result, CHART_PATH)}")
                else:
                    print("Serve un risultato con due colonne: etichetta e numero.")
                continue
            if not text:
                continue
            answer, result = await run_turn(llm, model, mcp_client, tools, history,
                                            text, confirm, trace = trace)
            last_result = result or last_result
            print(f"\nAgente: {answer}")
            
if __name__ == "__main__":
    asyncio.run(main())
        
    