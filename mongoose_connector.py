#!/usr/bin/env python3
"""
Mongoose OS Connector - Device communication interface for Infinity Research Portal
Handles communication with Mongoose OS devices and firmware integration
"""

import os
import json
import socket
import requests
from datetime import datetime, timezone


# Configuration
Z_ROOT = os.path.abspath(os.path.dirname(__file__))
MONGOOSE_CONFIG = os.path.join(Z_ROOT, "mongoose", "mongoose.json")


class MongooseConnector:
    """Handle connections and commands to Mongoose OS devices."""
    
    def __init__(self, config_path=MONGOOSE_CONFIG):
        """
        Initialize MongooseConnector.
        
        Args:
            config_path: Path to mongoose.json configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.operator = self.config.get("operator", "Unknown")
        self.mode = self.config.get("mode", "passive")
        
    def load_config(self):
        """Load Mongoose OS configuration."""
        if not os.path.exists(self.config_path):
            return {
                "operator": "System",
                "attached": datetime.now(timezone.utc).isoformat(),
                "mode": "passive"
            }
        
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def get_status(self):
        """
        Get current Mongoose OS configuration status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "success": True,
            "operator": self.operator,
            "mode": self.mode,
            "attached": self.config.get("attached"),
            "config_loaded": bool(self.config),
            "message": f"Mongoose OS connected - Operator: {self.operator}, Mode: {self.mode}"
        }
    
    def send_command(self, command, device_ip=None, device_port=80):
        """
        Send a command to a Mongoose OS device.
        
        Args:
            command: Command string to send
            device_ip: IP address of the device (optional)
            device_port: Port of the device (default: 80)
        
        Returns:
            Response dictionary
        """
        if not device_ip:
            return {
                "success": False,
                "error": "Device IP address required",
                "message": "No device configured. Please provide device IP."
            }
        
        try:
            # Try HTTP RPC call (Mongoose OS default interface)
            url = f"http://{device_ip}:{device_port}/rpc"
            
            # Parse command - basic command format
            if command.startswith("/"):
                # RPC-style command
                method = command.strip("/").split()[0]
                params = {}
            else:
                # Free-form command - use Sys.GetInfo as default
                method = "Sys.GetInfo"
                params = {}
            
            payload = {
                "method": method,
                "params": params
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "command": command,
                    "response": data,
                    "message": f"Command executed: {command}"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": f"Device returned error: {response.status_code}"
                }
        
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Connection timeout",
                "message": "Device did not respond in time"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection failed",
                "message": "Could not connect to device. Check IP and network."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Command execution failed: {str(e)}"
            }
    
    def get_device_info(self, device_ip=None):
        """
        Get device information from Mongoose OS.
        
        Args:
            device_ip: IP address of the device
        
        Returns:
            Device information dictionary
        """
        return self.send_command("Sys.GetInfo", device_ip)
    
    def get_available_commands(self):
        """
        Get list of available Mongoose OS commands.
        
        Returns:
            List of command descriptions
        """
        commands = [
            {
                "command": "status",
                "description": "Get Mongoose OS connector status",
                "usage": "status"
            },
            {
                "command": "info",
                "description": "Get device system information",
                "usage": "info <device_ip>"
            },
            {
                "command": "help",
                "description": "Show available commands",
                "usage": "help"
            },
            {
                "command": "/rpc/Sys.GetInfo",
                "description": "RPC call to get system information",
                "usage": "/rpc/Sys.GetInfo <device_ip>"
            },
            {
                "command": "/rpc/Config.Get",
                "description": "RPC call to get device configuration",
                "usage": "/rpc/Config.Get <device_ip>"
            }
        ]
        
        return {
            "success": True,
            "commands": commands,
            "message": f"Available commands: {len(commands)}"
        }
    
    def parse_chat_command(self, message):
        """
        Parse a chat message and execute corresponding command.
        
        Args:
            message: User chat message/command
        
        Returns:
            Response dictionary
        """
        message = message.strip()
        
        if not message:
            return {
                "success": False,
                "error": "Empty command",
                "message": "Please enter a command. Type 'help' for available commands."
            }
        
        # Parse command
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle built-in commands
        if command == "status":
            return self.get_status()
        
        elif command == "help":
            return self.get_available_commands()
        
        elif command == "info":
            if not args:
                return {
                    "success": False,
                    "error": "Missing device IP",
                    "message": "Usage: info <device_ip>"
                }
            return self.get_device_info(args[0])
        
        elif message.startswith("/rpc/"):
            # RPC command
            if not args:
                return {
                    "success": False,
                    "error": "Missing device IP",
                    "message": "Usage: /rpc/Method <device_ip>"
                }
            return self.send_command(message, args[-1])
        
        else:
            return {
                "success": False,
                "error": "Unknown command",
                "message": f"Unknown command: {command}. Type 'help' for available commands."
            }


# ------------------------------ API FOR FLASK INTEGRATION ------------------------------

def create_mongoose_routes(app):
    """
    Create Flask routes for Mongoose OS integration.
    
    Args:
        app: Flask application instance
    """
    connector = MongooseConnector()
    
    @app.route('/api/mongoose/status', methods=['GET'])
    def mongoose_status():
        """Get Mongoose OS status."""
        return connector.get_status()
    
    @app.route('/api/mongoose/commands', methods=['GET'])
    def mongoose_commands():
        """Get available commands."""
        return connector.get_available_commands()
    
    @app.route('/api/mongoose/chat', methods=['POST'])
    def mongoose_chat():
        """
        Process chat command.
        Requires authentication.
        """
        from flask import request, session, jsonify
        
        # Check authentication
        if 'session_token' not in session:
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "message": "Please log in to use the chat terminal."
            }), 401
        
        data = request.get_json() or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Empty message",
                "message": "Please enter a command."
            }), 400
        
        # Parse and execute command
        response = connector.parse_chat_command(message)
        
        return jsonify(response)


# ------------------------------ CLI INTERFACE ------------------------------

def main():
    """CLI interface for Mongoose OS connector."""
    import sys
    
    connector = MongooseConnector()
    
    print("∞ Mongoose OS Connector - Infinity Research Portal ∞")
    print("=" * 60)
    
    status = connector.get_status()
    print(f"Operator: {status['operator']}")
    print(f"Mode: {status['mode']}")
    print(f"Attached: {status.get('attached', 'Unknown')}")
    print("=" * 60)
    print("Type 'help' for commands, 'quit' to exit")
    print()
    
    while True:
        try:
            message = input("mongoose> ").strip()
            
            if not message:
                continue
            
            if message.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            result = connector.parse_chat_command(message)
            
            if result.get('success'):
                if 'commands' in result:
                    # Help command
                    print("\nAvailable commands:")
                    for cmd in result['commands']:
                        print(f"  {cmd['command']:<20} - {cmd['description']}")
                        print(f"  {'':20}   Usage: {cmd['usage']}")
                    print()
                elif 'response' in result:
                    # Device response
                    print(f"\nResponse: {json.dumps(result['response'], indent=2)}\n")
                else:
                    # Status or other message
                    print(f"\n{result.get('message', 'Success')}\n")
            else:
                print(f"\n❌ Error: {result.get('message', 'Unknown error')}\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
