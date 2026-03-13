#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Tools - Unified interface for trading tools

Author: Peter Tokmakov
Version: 1.0.0

Modules:
- Generate Signals
- PnL Calculator
- PrintLvl
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from datetime import datetime
from pathlib import Path
import asyncio
import threading
import logging

# Ќ бва®©Є  «®ЈЁа®ў ­Ёп
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Џ®«гз Ґ¬ ¤ЁаҐЄв®аЁо, Ј¤Ґ ­ е®¤Ёвбп бЄаЁЇв
SCRIPT_DIR = Path(__file__).parent
STATIC_DIR = SCRIPT_DIR / "static"
MODULES_DIR = SCRIPT_DIR / "modules"

# €¬Ї®авЁагҐ¬ ¬®¤г«Ё
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(MODULES_DIR))

# ‘®§¤ с¬ FastAPI ЇаЁ«®¦Ґ­ЁҐ
app = FastAPI(
    title="Trading Tools",
    description="Unified interface for trading tools",
    version="1.0.0"
)

# Њ®­вЁагҐ¬ бв вЁзҐбЄЁҐ д ©«л
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop = None
        self._message_queue = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected, total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected, total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        logger.info(f"Broadcasting to {len(self.active_connections)} connections: {message[:100]}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to connection: {e}")

    async def process_queue(self):
        """Process messages from queue"""
        while True:
            try:
                message = await self._message_queue.get()
                await self.broadcast(message)
            except Exception as e:
                logger.error(f"Error processing queue: {e}")

    def broadcast_sync(self, message: str):
        """Synchronous broadcast for background threads"""
        logger.info(f"broadcast_sync called: {message[:100]}")
        if self._message_queue is None:
            logger.error("broadcast_sync: No message queue!")
            return

        if self._loop is None:
            logger.error("broadcast_sync: No event loop!")
            return

        try:
            self._loop.call_soon_threadsafe(self._message_queue.put_nowait, message)
            logger.info(f"broadcast_sync: Message put in queue")
        except Exception as e:
            logger.error(f"broadcast_sync: Error: {e}")

manager = ConnectionManager()

# ==================== MODELS ====================

class PnLCalculateRequest(BaseModel):
    start_date: str
    end_date: str
    tab_id: Optional[str] = "pnl-calculator"

class PrintLvlRunRequest(BaseModel):
    ticker: str
    date: str
    time: str
    start_time_offset: str = "0"
    end_time_offset: str = "1000"
    tab_id: Optional[str] = "printlvl"

class PrintLvlSavePdfRequest(BaseModel):
    output_path: str
    tab_id: Optional[str] = "printlvl"

class GenerateSignalsRunRequest(BaseModel):
    start_date: str
    end_date: str
    run_features_calculator: bool = True
    run_rscript: bool = True
    run_signal_processing: bool = True
    run_cleanup: bool = True
    tab_id: Optional[str] = "generate-signals"


# ==================== API ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """ѓ« ў­ п бва ­Ёж """
    index_path = STATIC_DIR / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

# ==================== PnL Calculator ====================

@app.post("/api/pnl-calculator/calculate")
async def pnl_calculator_calculate(request: PnLCalculateRequest, background_tasks: BackgroundTasks):
    """ђ бзсв PnL"""
    logger.info(f"PnL Calculator request: {request.start_date} - {request.end_date}")
    tab_id = request.tab_id or "pnl-calculator"
    
    try:
        from modules.pnl_calculator import PnLCalculator

        def log_callback(message: str, level: str = "info"):
            logger.info(f"log_callback: {message}")
            manager.broadcast_sync(json.dumps({
                'type': 'log',
                'tab_id': tab_id,
                'message': message,
                'level': level,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }))

        def run_calculation():
            logger.info("run_calculation: Starting...")
            try:
                calculator = PnLCalculator(SCRIPT_DIR)
                result = calculator.calculate_pnl(
                    start_date=request.start_date,
                    end_date=request.end_date,
                    log_callback=log_callback
                )
                
                logger.info(f"run_calculation: Result: {result['status']}")
                manager.broadcast_sync(json.dumps({
                    'type': 'result',
                    'tab_id': tab_id,
                    'result': result
                }))
            except Exception as e:
                logger.error(f"run_calculation: Error: {e}")
                manager.broadcast_sync(json.dumps({
                    'type': 'error',
                    'tab_id': tab_id,
                    'message': str(e)
                }))

        logger.info("Adding background task...")
        background_tasks.add_task(run_calculation)

        return {
            "status": "started",
            "message": "ђ бзсв PnL § ЇгйҐ­",
            "start_date": request.start_date,
            "end_date": request.end_date
        }
    except Exception as e:
        logger.error(f"PnL Calculator error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pnl-calculator/strategies")
async def pnl_calculator_strategies():
    """Џ®«гзЁвм бЇЁб®Є бва вҐЈЁ©"""
    try:
        from modules.pnl_calculator import PnLCalculator

        calculator = PnLCalculator(SCRIPT_DIR)
        strategies = calculator.get_strategies()

        return {
            "strategies": strategies
        }
    except Exception as e:
        logger.error(f"PnL Strategies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PrintLvl ====================

printlvl_instance = None
generate_signals_instance = None

@app.post("/api/printlvl/run")
async def printlvl_run(request: PrintLvlRunRequest, background_tasks: BackgroundTasks):
    """‡ ЇгбЄ PrintLvl pipeline"""
    global printlvl_instance
    
    logger.info(f"PrintLvl request: {request.ticker} {request.date}")
    tab_id = request.tab_id or "printlvl"
    
    try:
        from modules.printlvl_api import PrintLvl

        def log_callback(message: str, level: str = "info"):
            logger.info(f"log_callback: {message}")
            manager.broadcast_sync(json.dumps({
                'type': 'log',
                'tab_id': tab_id,
                'message': message,
                'level': level,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }))

        def run_pipeline():
            logger.info("run_pipeline: Starting...")
            global printlvl_instance
            
            try:
                printlvl_instance = PrintLvl(SCRIPT_DIR, log_callback=log_callback)
                
                config_params = {
                    'ticker': request.ticker,
                    'date': request.date,
                    'time': request.time,
                    'start_time_offset': request.start_time_offset,
                    'end_time_offset': request.end_time_offset
                }
                
                result = printlvl_instance.run_pipeline(config_params)
                
                logger.info(f"run_pipeline: Result: {result['status']}")
                manager.broadcast_sync(json.dumps({
                    'type': 'result',
                    'tab_id': tab_id,
                    'result': result
                }))
            except Exception as e:
                logger.error(f"run_pipeline: Error: {e}")
                manager.broadcast_sync(json.dumps({
                    'type': 'error',
                    'tab_id': tab_id,
                    'message': str(e)
                }))

        logger.info("Adding background task...")
        background_tasks.add_task(run_pipeline)

        return {
            "status": "started",
            "message": "PrintLvl pipeline § ЇгйҐ­",
            "ticker": request.ticker,
            "date": request.date
        }
    except Exception as e:
        logger.error(f"PrintLvl error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/printlvl/save-pdf")
async def printlvl_save_pdf(request: PrintLvlSavePdfRequest, background_tasks: BackgroundTasks):
    """‘®еа ­Ґ­ЁҐ PDF"""
    global printlvl_instance
    
    logger.info(f"PrintLvl save PDF request: {request.output_path}")
    tab_id = request.tab_id or "printlvl"
    
    try:
        if printlvl_instance is None:
            raise HTTPException(status_code=400, detail="PrintLvl instance not found. Run pipeline first.")
        
        def save_pdf():
            logger.info("save_pdf: Starting...")
            try:
                result = printlvl_instance.save_pdf(request.output_path)
                
                logger.info(f"save_pdf: Result: {result['status']}")
                manager.broadcast_sync(json.dumps({
                    'type': 'result',
                    'tab_id': tab_id,
                    'result': result
                }))
            except Exception as e:
                logger.error(f"save_pdf: Error: {e}")
                manager.broadcast_sync(json.dumps({
                    'type': 'error',
                    'tab_id': tab_id,
                    'message': str(e)
                }))

        logger.info("Adding background task...")
        background_tasks.add_task(save_pdf)

        return {
            "status": "started",
            "message": "‘®еа ­Ґ­ЁҐ PDF § ЇгйҐ­®",
            "output_path": request.output_path
        }
    except Exception as e:
        logger.error(f"PrintLvl save PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Generate Signals ====================

@app.post("/api/generate-signals/run")
async def generate_signals_run(request: GenerateSignalsRunRequest, background_tasks: BackgroundTasks):
    """Run signal generation"""
    global generate_signals_instance
    logger.info(f"Generate Signals: {request.start_date} - {request.end_date}")
    try:
        from modules.generate_signals import GenerateSignals
        def log_callback(message: str, level: str = "info"):
            manager.broadcast_sync(json.dumps({
                'type': 'log', 'tab_id': 'generate-signals', 'message': message, 
                'level': level, 
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }))
        def log_fc_callback(message: str):
            manager.broadcast_sync(json.dumps({
                'type': 'log_fc', 'tab_id': 'generate-signals', 'message': message,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }))
        def run_generation():
            global generate_signals_instance
            try:
                logger.info("[DEBUG] run_generation started")
                import yaml
                config_path = SCRIPT_DIR / "configs" / "generate_signals.yaml"
                logger.info(f"[DEBUG] config_path: {config_path}, exists: {config_path.exists()}")
                settings = yaml.safe_load(open(config_path)) if config_path.exists() else {}
                logger.info(f"[DEBUG] settings loaded: {list(settings.keys()) if settings else 'None'}")
                generate_signals_instance = GenerateSignals(settings)
                logger.info("[DEBUG] GenerateSignals instance created")
                result = generate_signals_instance.generate(
                    start_date=request.start_date, 
                    end_date=request.end_date,
                    run_features_calculator=request.run_features_calculator,
                    run_rscript=request.run_rscript,
                    run_signal_processing=request.run_signal_processing,
                    run_cleanup=request.run_cleanup, 
                    log_callback=log_callback,
                    log_fc_callback=log_fc_callback
                )
                manager.broadcast_sync(json.dumps({'type': 'result', 'result': result}))
            except Exception as e:
                manager.broadcast_sync(json.dumps({'type': 'error', 'message': str(e)}))
        background_tasks.add_task(run_generation)
        return {'status': 'started', 'message': 'Generation started'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate-signals/status")
async def generate_signals_status():
    """Get signal generation status"""
    global generate_signals_instance
    if generate_signals_instance is None:
        return {'status': 'idle', 'message': 'Not running'}
    return {'status': 'running', 'message': 'In progress'}

# ==================== WebSocket ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint ¤«п real-time updates"""
    logger.info("WebSocket connection request")
    await manager.connect(websocket)
    manager._loop = asyncio.get_running_loop()
    logger.info(f"Event loop stored: {manager._loop}")
    
    manager._message_queue = asyncio.Queue()
    logger.info("Message queue created")
    
    asyncio.create_task(manager.process_queue())
    logger.info("Queue processor started")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"WebSocket received: {data}")
            await manager.broadcast(data)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8505)
