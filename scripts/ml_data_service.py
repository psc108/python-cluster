#!/usr/bin/env python3
"""
ML Data Collection Service - Phase 4.1
Continuous data collection for ML training
"""

import time
import schedule
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.ml_data_collector import MLDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLDataService:
    def __init__(self):
        self.collector = MLDataCollector()
        self.running = True
        
    def collect_metrics_job(self):
        """Scheduled job to collect metrics"""
        try:
            logger.info("Collecting ML training data...")
            metrics = self.collector.collect_enhanced_metrics()
            
            if metrics:
                self.collector.store_metrics(metrics)
                logger.info(f"Collected {len(metrics)} metrics")
                
                # Check if ready for ML training
                summary = self.collector.get_data_summary()
                if summary['ready_for_ml']:
                    logger.info(f"ML training data ready: {summary['total_points']} data points")
                else:
                    needed = 1000 - summary['total_points']
                    logger.info(f"Need {needed} more data points for ML training")
            else:
                logger.warning("No metrics collected")
                
        except Exception as e:
            logger.error(f"Error in collection job: {e}")
    
    def start(self):
        """Start the data collection service"""
        logger.info("Starting ML Data Collection Service")
        
        # Schedule collection every 2 minutes (faster data accumulation)
        schedule.every(2).minutes.do(self.collect_metrics_job)
        
        # Initial collection
        self.collect_metrics_job()
        
        # Run scheduler
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except KeyboardInterrupt:
                logger.info("Stopping ML Data Collection Service")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    service = MLDataService()
    service.start()