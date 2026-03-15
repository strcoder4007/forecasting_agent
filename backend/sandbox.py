import subprocess
import os
import tempfile
import sys
import traceback

def execute_python(code: str, timeout: int = 120) -> str:
    """Executes a string of Python code in a temporary file and returns stdout and stderr.
    
    Useful for data exploration, ETL, and model training.
    
    Args:
        code: The raw python code to execute. Do not include markdown formatting (like ```python).
        timeout: Maximum execution time in seconds.
        
    Returns:
        A string containing the combined stdout and stderr of the script execution.
    """
    # Clean up the code if the LLM accidentally wrapped it in markdown
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
        
    code = code.strip()

    # Create a temporary file to hold the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        # Get the python executable currently running this backend
        python_executable = sys.executable
        
        # Execute the script in a subprocess
        result = subprocess.run(
            [python_executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = []
        if result.stdout:
            output.append("=== STDOUT ===")
            output.append(result.stdout)
        if result.stderr:
            output.append("=== STDERR ===")
            output.append(result.stderr)
            
        if not output:
            return "Script executed successfully with no output."
            
        return "\n".join(output)
        
    except subprocess.TimeoutExpired:
        return f"Error: Script execution timed out after {timeout} seconds."
    except Exception as e:
        return f"System Error executing script: {str(e)}\n{traceback.format_exc()}"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
