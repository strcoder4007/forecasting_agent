import os
import duckdb
import pandas as pd
from google import genai
from google.genai import types

class ChatService:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
        self.model = "gemini-2.5-flash"

    def chat(self, user_query: str, run_results: list = None) -> str:
        # Check if the user is asking to run a forecast
        intent_prompt = f"""
        You are an AI assistant for a retail demand forecasting system. 
        Determine if the user's intent is to run, start, or trigger a new forecast.
        If yes, respond with EXACTLY the string: [START_FORECAST]
        If no, respond with EXACTLY the string: [NO]
        
        User: {user_query}
        """
        
        try:
            intent_response = self.client.models.generate_content(
                model=self.model,
                contents=intent_prompt
            )
            if "[START_FORECAST]" in intent_response.text.strip().upper():
                return "[START_FORECAST]"
        except Exception as e:
            return f"Error checking intent: {str(e)}"

        if not run_results:
            # General conversation without a run context
            general_prompt = f"""
            You are a helpful AI assistant for a retail demand forecasting system.
            The user hasn't run a forecast yet. Encourage them to ask you to run a forecast.
            
            User: {user_query}
            """
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=general_prompt
                )
                return response.text
            except Exception as e:
                return f"Error: {str(e)}"

        # If run_results is present, execute DuckDB query
        results_df = pd.DataFrame(run_results)
        stores_df = self.data_loader.load_stores()
        items_df = self.data_loader.load_items()
        stock_df = self.data_loader.load_stock()
        sales_df = self.data_loader.load_sales()

        schema_context = f"""
        You are a highly capable data analyst AI. You answer user questions by writing a DuckDB SQL query, 
        executing it, and summarizing the result.

        You have access to the following tables in DuckDB (they are Pandas DataFrames):

        Table: results_df (The final forecast output)
        Columns: {', '.join(results_df.columns)}

        Table: stores_df (Store metadata)
        Columns: {', '.join(stores_df.columns)}

        Table: items_df (Item metadata)
        Columns: {', '.join(items_df.columns)}

        Table: stock_df (Raw stock-on-hand history)
        Columns: {', '.join(stock_df.columns)}

        Table: sales_df (Raw sales history)
        Columns: {', '.join(sales_df.columns)}

        Task: Write a SQL query to answer the user's question. 
        Only return the raw SQL query. Do NOT wrap it in markdown block quotes (```sql). 
        Do not add any explanations.
        DuckDB can query these tables directly by their names (e.g., SELECT * FROM results_df).
        """

        try:
            sql_response = self.client.models.generate_content(
                model=self.model,
                contents=f"{schema_context}\n\nUser Question: {user_query}"
            )
            sql_query = sql_response.text.strip().replace("```sql", "").replace("```", "").strip()

            result_df = duckdb.query(sql_query).df()
            
            synthesis_prompt = f"""
            User Question: {user_query}
            
            SQL Query Used:
            {sql_query}
            
            Query Results (Markdown):
            {result_df.to_markdown(index=False)}
            
            Based on the query results, provide a clear, concise, and professional answer to the user's question.
            """
            
            final_response = self.client.models.generate_content(
                model=self.model,
                contents=synthesis_prompt
            )
            
            return final_response.text
            
        except Exception as e:
            return f"I encountered an error trying to process your request: {str(e)}"
