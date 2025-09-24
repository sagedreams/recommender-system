"""
Audit Logger for Data Processing
Tracks all data processing steps, errors, and quality metrics
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

class AuditLogger:
    """Comprehensive audit logging for data processing"""
    
    def __init__(self, log_file: str = "data_processing_audit.log"):
        self.log_file = log_file
        self.setup_logging()
        
        # Audit tracking
        self.processing_stats = {
            "start_time": None,
            "end_time": None,
            "total_records_processed": 0,
            "total_records_skipped": 0,
            "total_records_errors": 0,
            "unique_orders": 0,
            "unique_items": 0,
            "cooccurrence_pairs": 0
        }
        
        self.skipped_records = []
        self.error_records = []
        self.quality_metrics = {}
        
    def setup_logging(self):
        """Setup structured logging"""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/{self.log_file}"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_processing(self, file_path: str):
        """Log start of data processing"""
        self.processing_stats["start_time"] = datetime.utcnow().isoformat()
        self.logger.info(f"Starting data processing for file: {file_path}")
        self.logger.info(f"Processing started at: {self.processing_stats['start_time']}")
    
    def log_record_processed(self, record: Dict[str, Any]):
        """Log successful record processing"""
        self.processing_stats["total_records_processed"] += 1
        
        if self.processing_stats["total_records_processed"] % 10000 == 0:
            self.logger.info(f"Processed {self.processing_stats['total_records_processed']} records")
    
    def log_record_skipped(self, record: Dict[str, Any], reason: str, line_number: Optional[int] = None):
        """Log skipped record with reason"""
        self.processing_stats["total_records_skipped"] += 1
        
        skipped_record = {
            "line_number": line_number,
            "record": record,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.skipped_records.append(skipped_record)
        self.logger.warning(f"Record skipped at line {line_number}: {reason} - {record}")
    
    def log_record_error(self, record: Dict[str, Any], error: str, line_number: Optional[int] = None):
        """Log record processing error"""
        self.processing_stats["total_records_errors"] += 1
        
        error_record = {
            "line_number": line_number,
            "record": record,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.error_records.append(error_record)
        self.logger.error(f"Error processing record at line {line_number}: {error} - {record}")
    
    def log_data_quality_metrics(self, metrics: Dict[str, Any]):
        """Log data quality metrics"""
        self.quality_metrics.update(metrics)
        self.logger.info(f"Data quality metrics: {json.dumps(metrics, indent=2)}")
    
    def log_cooccurrence_stats(self, total_items: int, total_pairs: int):
        """Log co-occurrence matrix statistics"""
        self.processing_stats["unique_items"] = total_items
        self.processing_stats["cooccurrence_pairs"] = total_pairs
        self.logger.info(f"Co-occurrence matrix: {total_items} items, {total_pairs} pairs")
    
    def log_order_stats(self, total_orders: int):
        """Log order statistics"""
        self.processing_stats["unique_orders"] = total_orders
        self.logger.info(f"Total unique orders: {total_orders}")
    
    def end_processing(self):
        """Log end of data processing and generate summary"""
        self.processing_stats["end_time"] = datetime.utcnow().isoformat()
        
        # Calculate processing time
        if self.processing_stats["start_time"]:
            start = datetime.fromisoformat(self.processing_stats["start_time"])
            end = datetime.fromisoformat(self.processing_stats["end_time"])
            processing_time = (end - start).total_seconds()
            self.processing_stats["processing_time_seconds"] = processing_time
        
        # Generate summary
        self.logger.info("="*50)
        self.logger.info("DATA PROCESSING SUMMARY")
        self.logger.info("="*50)
        self.logger.info(f"Processing time: {processing_time:.2f} seconds")
        self.logger.info(f"Total records processed: {self.processing_stats['total_records_processed']}")
        self.logger.info(f"Total records skipped: {self.processing_stats['total_records_skipped']}")
        self.logger.info(f"Total records with errors: {self.processing_stats['total_records_errors']}")
        self.logger.info(f"Unique orders: {self.processing_stats['unique_orders']}")
        self.logger.info(f"Unique items: {self.processing_stats['unique_items']}")
        self.logger.info(f"Co-occurrence pairs: {self.processing_stats['cooccurrence_pairs']}")
        
        # Data quality summary
        if self.quality_metrics:
            self.logger.info("Data Quality Metrics:")
            for metric, value in self.quality_metrics.items():
                self.logger.info(f"  {metric}: {value}")
        
        # Error summary
        if self.error_records:
            self.logger.warning(f"Total errors: {len(self.error_records)}")
            error_types = Counter([error["error"] for error in self.error_records])
            for error_type, count in error_types.most_common():
                self.logger.warning(f"  {error_type}: {count} occurrences")
        
        # Skip reasons summary
        if self.skipped_records:
            self.logger.warning(f"Total skipped records: {len(self.skipped_records)}")
            skip_reasons = Counter([skip["reason"] for skip in self.skipped_records])
            for reason, count in skip_reasons.most_common():
                self.logger.warning(f"  {reason}: {count} occurrences")
        
        self.logger.info("="*50)
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        report = {
            "processing_summary": self.processing_stats,
            "quality_metrics": self.quality_metrics,
            "error_summary": {
                "total_errors": len(self.error_records),
                "error_types": dict(Counter([error["error"] for error in self.error_records])),
                "sample_errors": self.error_records[:10]  # First 10 errors
            },
            "skip_summary": {
                "total_skipped": len(self.skipped_records),
                "skip_reasons": dict(Counter([skip["reason"] for skip in self.skipped_records])),
                "sample_skipped": self.skipped_records[:10]  # First 10 skipped
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return report
    
    def save_audit_report(self, filename: str = None):
        """Save audit report to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/audit_report_{timestamp}.json"
        
        report = self.generate_audit_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Audit report saved to: {filename}")
        return filename
