#!/usr/bin/env python3
"""
Test MCP client for sending requests to the SeferFlow MCP server.

Usage:
  # In one terminal, start seferflow:
  ./seferflow

  # In another terminal, run this script:
  python3 test_mcp_client.py
"""

import socket
import json
import sys
import time

def send_mcp_request(host: str, port: int, method: str, params: dict = None) -> dict:
    """Send a JSON-RPC 2.0 request to MCP server and return response."""
    req_id = 1

    if method == "tools/list":
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method
        }
    elif method == "tools/call":
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": {
                "name": "say_text",
                "arguments": params or {}
            }
        }
    else:
        raise ValueError(f"Unknown method: {method}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.sendall((json.dumps(req) + '\n').encode())

        # Receive response (read until newline)
        data = b""
        sock.settimeout(30.0)
        while b'\n' not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk

        sock.close()
        resp = json.loads(data.decode().strip())
        return resp

    except ConnectionRefusedError:
        return {"error": "Connection refused — MCP server not running"}
    except socket.timeout:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}

def main():
    host = "127.0.0.1"
    port = 8765

    print("="*70)
    print("MCP CLIENT TEST")
    print("="*70)
    print(f"\nConnecting to {host}:{port}...\n")

    # Test 1: List tools
    print("TEST 1: List available tools")
    print("-" * 70)
    resp = send_mcp_request(host, port, "tools/list")
    if "error" in resp:
        print(f"❌ Error: {resp['error']}")
        print("   (Make sure seferflow is running: ./seferflow)")
        return 1

    print(json.dumps(resp, indent=2))

    if "result" in resp and "tools" in resp["result"]:
        tools = resp["result"]["tools"]
        if tools:
            tool = tools[0]
            print(f"\n✅ Found tool: {tool['name']}")
            print(f"   Description: {tool['description']}")
        else:
            print("❌ No tools returned")
            return 1
    else:
        print("❌ No result or tools in response")
        return 1

    # Test 2: Call say_text (this will only work if book is playing)
    print("\n" + "="*70)
    print("TEST 2: Call say_text tool")
    print("-" * 70)
    print("Note: This requires seferflow to be playing audio")
    print("Sending test message...\n")

    text = "This is a test message from the MCP server."
    resp = send_mcp_request(host, port, "tools/call", {"text": text})
    print(json.dumps(resp, indent=2))

    if "result" in resp:
        print("\n✅ Successfully sent interrupt request")
    elif "error" in resp:
        error_code = resp["error"].get("code", -1)
        error_msg = resp["error"].get("message", "Unknown error")

        if error_code == -32602:
            print(f"\n❌ Validation error: {error_msg}")
        elif error_code == -32603:
            print(f"\n❌ Server error: {error_msg}")
            print("   (This might mean no book is currently playing)")
        else:
            print(f"\n❌ Error ({error_code}): {error_msg}")

    print("\n" + "="*70)
    print("MCP CLIENT TEST COMPLETE")
    print("="*70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
