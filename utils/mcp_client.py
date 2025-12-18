import subprocess
import json
import sys
import os
import threading
import queue

class MCPClient:
    def __init__(self, server_script_path):
        self.server_script_path = server_script_path
        self.process = None
        self.request_id = 0
        self.pending_requests = {}
        self.running = False

    def start(self):
        """Starts the MCP server subprocess."""
        env = os.environ.copy()
        python_exe = sys.executable
        
        self.process = subprocess.Popen(
            [python_exe, self.server_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr, # Forward stderr to see logs
            env=env,
            text=True,
            bufsize=1 # Line buffered
        )
        self.running = True
        
        # Start reader thread
        self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.reader_thread.start()

    def stop(self):
        """Stops the MCP server subprocess."""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process = None

    def _read_loop(self):
        """Reads JSON-RPC responses from the server."""
        while self.running and self.process:
            line = self.process.stdout.readline()
            if not line:
                break
            try:
                response = json.loads(line)
                if "id" in response and response["id"] in self.pending_requests:
                    # Complete the future/queue
                    self.pending_requests[response["id"]].put(response)
                    del self.pending_requests[response["id"]]
            except json.JSONDecodeError:
                pass # Ignore non-JSON lines (logs)

    def call_tool(self, tool_name, arguments):
        """Calls a tool on the MCP server."""
        if not self.process:
            raise RuntimeError("MCP Client is not started.")

        self.request_id += 1
        current_id = self.request_id
        
        # Create a queue to wait for response
        response_queue = queue.Queue()
        self.pending_requests[current_id] = response_queue
        
        # Construct JSON-RPC request
        # Note: FastMCP uses a specific protocol. 
        # Standard MCP protocol for tools usually involves "tools/call".
        # Let's try the standard format.
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": current_id
        }
        
        # Send request
        try:
            json_str = json.dumps(request)
            self.process.stdin.write(json_str + "\n")
            self.process.stdin.flush()
        except Exception as e:
            del self.pending_requests[current_id]
            raise e
            
        # Wait for response
        try:
            response = response_queue.get(timeout=30) # 30s timeout
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")
            
            # Result is usually in result.content or similar depending on protocol version
            # FastMCP returns result directly in 'result' usually?
            # Let's inspect the response structure if we hit errors.
            return response.get("result", {}).get("content", [])
            
        except queue.Empty:
            del self.pending_requests[current_id]
            raise TimeoutError("MCP Tool call timed out.")

# Global client instance
client = None

def get_client():
    global client
    if client is None:
        # Assuming server.py is in mcp_server/server.py relative to project root
        # We need absolute path
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        server_path = os.path.join(base_path, 'mcp_server', 'server.py')
        client = MCPClient(server_path)
        client.start()
    return client
