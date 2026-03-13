#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintLvl API - Wrapper for PrintLvl functionality

Provides a programmatic interface to PrintLvl without GUI.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# Import functions from printlvl module
try:
    from modules.printlvl import (
        parse_config_txt,
        save_config_txt,
        update_config_json,
        connect_ssh,
        ensure_remote_dir,
        upload_config,
        run_simulator,
        read_file_from_server,
        load_data_from_server,
        process_data,
        plot_lvl2_with_orders,
        generate_pdfs
    )
except ImportError:
    # Fallback for direct import
    import importlib.util
    spec = importlib.util.spec_from_file_location("printlvl", Path(__file__).parent / "printlvl.py")
    printlvl_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(printlvl_module)
    
    parse_config_txt = printlvl_module.parse_config_txt
    save_config_txt = printlvl_module.save_config_txt
    update_config_json = printlvl_module.update_config_json
    connect_ssh = printlvl_module.connect_ssh
    ensure_remote_dir = printlvl_module.ensure_remote_dir
    upload_config = printlvl_module.upload_config
    run_simulator = printlvl_module.run_simulator
    read_file_from_server = printlvl_module.read_file_from_server
    load_data_from_server = printlvl_module.load_data_from_server
    process_data = printlvl_module.process_data
    plot_lvl2_with_orders = printlvl_module.plot_lvl2_with_orders
    generate_pdfs = printlvl_module.generate_pdfs


class PrintLvl:
    """API wrapper for PrintLvl functionality."""
    
    def __init__(self, base_dir: Path, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize PrintLvl API.
        
        Args:
            base_dir: Base directory for config files
            log_callback: Optional callback for logging (message, level)
        """
        self.base_dir = Path(base_dir)
        self.log_callback = log_callback or (lambda msg, lvl: None)
        self.ssh = None
        self.config_params = {}
        self.df = None
        self.breaks_for_plot = None
        
    def _log(self, message: str, level: str = "info"):
        """Log message via callback."""
        if self.log_callback:
            self.log_callback(message, level)
    
    def run_pipeline(self, config_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete PrintLvl pipeline.
        
        Args:
            config_params: Configuration parameters
                - ticker: Ticker symbol (e.g., "MGNT_TQBR")
                - date: Date string (e.g., "11.12.2025")
                - time: Time string (e.g., "22:59:51.000")
                - start_time_offset: Start offset in ms (default: "0")
                - end_time_offset: End offset in ms (default: "1000")
        
        Returns:
            Dict with status and result
        """
        try:
            self.config_params = config_params
            self._log(f"Starting PrintLvl pipeline for {config_params.get('ticker', 'unknown')}", "info")
            
            # Connect to SSH
            self._log("Connecting to SSH...", "info")
            self.ssh = connect_ssh()
            if not self.ssh:
                return {"status": "error", "message": "Failed to connect to SSH"}
            
            # Create config files
            self._log("Creating config files...", "info")
            config_txt_path = self.base_dir / "config.txt"
            config_json_path = self.base_dir / "config.json"
            
            # Save config.txt
            save_config_txt(config_txt_path, config_params)
            
            # Update config.json
            update_config_json(config_json_path, config_params)
            
            # Upload config to server
            self._log("Uploading config to server...", "info")
            remote_config_path = "/path/to/remote/config.json"  # TODO: get from settings
            upload_config(self.ssh, config_txt_path, remote_config_path)
            
            # Run simulator
            self._log("Running simulator...", "info")
            simulator_path = "/path/to/simulator"  # TODO: get from settings
            run_simulator(self.ssh, simulator_path, config_json_path, 
                         log_print=lambda msg: self._log(msg, "info"))
            
            # Load data from server
            self._log("Loading data from server...", "info")
            data_path = f"/path/to/data/{config_params.get('ticker')}_{config_params.get('date')}.csv"
            self.df = load_data_from_server(self.ssh, data_path)
            
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data loaded from server"}
            
            # Process data
            self._log("Processing data...", "info")
            self.df, self.breaks_for_plot = process_data(self.df)
            
            self._log("Pipeline completed successfully", "info")
            return {
                "status": "success",
                "message": "Pipeline completed",
                "rows": len(self.df) if self.df is not None else 0
            }
            
        except Exception as e:
            self._log(f"Pipeline error: {str(e)}", "error")
            return {"status": "error", "message": str(e)}
    
    def save_pdf(self, output_path: str) -> Dict[str, Any]:
        """
        Save the generated plots as PDF.
        
        Args:
            output_path: Path to save the PDF
        
        Returns:
            Dict with status and result
        """
        try:
            if self.df is None:
                return {"status": "error", "message": "No data available. Run pipeline first."}
            
            self._log(f"Generating PDF: {output_path}", "info")
            
            # Generate PDFs
            generate_pdfs(
                self.df,
                self.breaks_for_plot,
                file_name_out=Path(output_path).stem,
                date=self.config_params.get('date', ''),
                output_dir=Path(output_path).parent
            )
            
            self._log(f"PDF saved: {output_path}", "info")
            return {"status": "success", "message": f"PDF saved to {output_path}"}
            
        except Exception as e:
            self._log(f"PDF generation error: {str(e)}", "error")
            return {"status": "error", "message": str(e)}
    
    def close(self):
        """Close SSH connection."""
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass
            self.ssh = None
