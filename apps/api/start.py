#!/usr/bin/env python
"""
Agno Multi-Agent Platform - Startup Script

Starts both backend (FastAPI) and frontend (Next.js) servers.

Usage:
    python start.py          # Start both servers
    python start.py backend  # Start only backend
    python start.py frontend # Start only frontend
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Print startup banner."""
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     █████╗  ██████╗ ███╗   ██╗ ██████╗                       ║
║    ██╔══██╗██╔════╝ ████╗  ██║██╔═══██╗                      ║
║    ███████║██║  ███╗██╔██╗ ██║██║   ██║                      ║
║    ██╔══██║██║   ██║██║╚██╗██║██║   ██║                      ║
║    ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝                      ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝                       ║
║                                                               ║
║           Multi-Agent Platform v3.0                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
""")


def check_dependencies():
    """Check if required dependencies are installed."""
    print(f"{Colors.YELLOW}🔍 Checking dependencies...{Colors.END}")
    
    # Check Python packages
    required_packages = ['fastapi', 'uvicorn', 'httpx']
    missing = []
    
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"{Colors.RED}❌ Missing packages: {', '.join(missing)}{Colors.END}")
        print(f"{Colors.YELLOW}Run: pip install -r requirements.txt{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✅ All Python dependencies OK{Colors.END}")
    return True


def start_backend():
    """Start the FastAPI backend server."""
    print(f"\n{Colors.BLUE}🚀 Starting Backend Server...{Colors.END}")
    
    root_dir = Path(__file__).parent
    
    return subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=root_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def start_frontend():
    """Start the Next.js frontend server."""
    print(f"\n{Colors.BLUE}🎨 Starting Frontend Server...{Colors.END}")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print(f"{Colors.YELLOW}📦 Installing frontend dependencies...{Colors.END}")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True,
    )


def print_status():
    """Print server status and URLs."""
    print(f"""
{Colors.GREEN}{Colors.BOLD}
═══════════════════════════════════════════════════════════════
                    🎉 SERVERS RUNNING
═══════════════════════════════════════════════════════════════

  📡 Backend API:     http://localhost:8000
  📚 API Docs:        http://localhost:8000/docs
  
  🎨 Frontend:        http://localhost:3000
  🔧 Flow Studio:     http://localhost:3000/flow-studio
  📊 Dashboard:       http://localhost:3000/dashboard
  💬 Chat:            http://localhost:3000/chat

═══════════════════════════════════════════════════════════════
  Press Ctrl+C to stop all servers
═══════════════════════════════════════════════════════════════
{Colors.END}
""")


def main():
    """Main entry point."""
    print_banner()
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if not check_dependencies():
        sys.exit(1)
    
    processes = []
    
    try:
        if mode in ["all", "backend"]:
            backend = start_backend()
            processes.append(("Backend", backend))
            time.sleep(2)  # Wait for backend to start
        
        if mode in ["all", "frontend"]:
            frontend = start_frontend()
            processes.append(("Frontend", frontend))
            time.sleep(3)  # Wait for frontend to start
        
        if mode == "all":
            print_status()
        
        # Keep running and show output
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"{Colors.RED}❌ {name} stopped unexpectedly{Colors.END}")
                    break
                
                # Read and print output
                line = proc.stdout.readline()
                if line:
                    prefix = f"[{name}]"
                    print(f"{Colors.BLUE}{prefix}{Colors.END} {line.strip()}")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Stopping servers...{Colors.END}")
        
        for name, proc in processes:
            proc.terminate()
            try:
                proc.wait(timeout=5)
                print(f"{Colors.GREEN}✅ {name} stopped{Colors.END}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"{Colors.YELLOW}⚠️ {name} killed{Colors.END}")
        
        print(f"{Colors.GREEN}👋 Goodbye!{Colors.END}")


if __name__ == "__main__":
    main()
