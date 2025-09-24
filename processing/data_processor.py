"""
Data processing pipeline for the recommender system
"""
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import logging
from audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process CSV data for recommendation system"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.df = None
        self.item_cooccurrence = defaultdict(lambda: defaultdict(int))
        self.item_frequency = Counter()
        self.order_items = defaultdict(list)
        self.audit_logger = AuditLogger()
        
    def load_data(self) -> pd.DataFrame:
        """Load and clean the CSV data"""
        try:
            self.audit_logger.start_processing(self.csv_file_path)
            logger.info(f"Loading data from {self.csv_file_path}")
            
            # Handle CSV with commas in item names by using proper quoting
            self.df = pd.read_csv(
                self.csv_file_path,
                quotechar='"',
                escapechar='\\',
                on_bad_lines='skip'  # Skip problematic lines
            )
            
            # Basic data cleaning
            self.df['item_name'] = self.df['item_name'].str.strip()
            original_count = len(self.df)
            self.df = self.df.dropna()
            cleaned_count = len(self.df)
            
            # Log data quality metrics
            quality_metrics = {
                "original_record_count": original_count,
                "cleaned_record_count": cleaned_count,
                "records_removed_na": original_count - cleaned_count,
                "unique_orders": self.df['order_id'].nunique(),
                "unique_items": self.df['item_name'].nunique(),
                "avg_order_size": len(self.df) / self.df['order_id'].nunique() if self.df['order_id'].nunique() > 0 else 0
            }
            
            self.audit_logger.log_data_quality_metrics(quality_metrics)
            self.audit_logger.log_order_stats(quality_metrics["unique_orders"])
            
            logger.info(f"Loaded {len(self.df)} records")
            logger.info(f"Unique orders: {self.df['order_id'].nunique()}")
            logger.info(f"Unique items: {self.df['item_name'].nunique()}")
            
            return self.df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.audit_logger.log_record_error({"file": self.csv_file_path}, str(e))
            raise
    
    def build_cooccurrence_matrix(self):
        """Build item-item co-occurrence matrix"""
        try:
            logger.info("Building co-occurrence matrix...")
            
            # Group items by order
            for order_id, group in self.df.groupby('order_id'):
                items = group['item_name'].tolist()
                self.order_items[order_id] = items
                
                # Count item frequencies
                for item in items:
                    self.item_frequency[item] += 1
                
                # Count co-occurrences
                for i, item1 in enumerate(items):
                    for j, item2 in enumerate(items):
                        if i != j:  # Don't count self-co-occurrence
                            self.item_cooccurrence[item1][item2] += 1
            
            logger.info(f"Built co-occurrence matrix for {len(self.item_cooccurrence)} items")
            self.audit_logger.log_cooccurrence_stats(len(self.item_cooccurrence), sum(len(items) for items in self.item_cooccurrence.values()))
        except Exception as e:
            logger.error(f"Error building co-occurrence matrix: {e}")
            self.audit_logger.log_record_error({"operation": "cooccurrence_matrix"}, str(e))
            raise
    
    def get_item_stats(self, item_name: str) -> Dict:
        """Get statistics for a specific item"""
        try:
            frequency = self.item_frequency.get(item_name, 0)
            cooccurring_items = len(self.item_cooccurrence.get(item_name, {}))
            
            # Get top co-occurring items
            top_cooccurring = []
            if item_name in self.item_cooccurrence:
                sorted_items = sorted(
                    self.item_cooccurrence[item_name].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                top_cooccurring = sorted_items[:10]
            
            return {
                "frequency": frequency,
                "cooccurring_items_count": cooccurring_items,
                "top_cooccurring": top_cooccurring,
                "popularity_rank": self._get_popularity_rank(item_name)
            }
        except Exception as e:
            logger.error(f"Error getting item stats for {item_name}: {e}")
            return {}
    
    def _get_popularity_rank(self, item_name: str) -> int:
        """Get popularity rank of an item"""
        try:
            sorted_items = sorted(
                self.item_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for rank, (item, _) in enumerate(sorted_items, 1):
                if item == item_name:
                    return rank
            return len(sorted_items) + 1
        except Exception as e:
            logger.error(f"Error getting popularity rank: {e}")
            return 0
    
    def get_popular_items(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular items"""
        try:
            sorted_items = sorted(
                self.item_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_items[:limit]
        except Exception as e:
            logger.error(f"Error getting popular items: {e}")
            return []
    
    def get_similar_items(self, item_name: str, limit: int = 10) -> List[Tuple[str, int]]:
        """Get items that frequently co-occur with the given item"""
        try:
            if item_name not in self.item_cooccurrence:
                return []
            
            sorted_items = sorted(
                self.item_cooccurrence[item_name].items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_items[:limit]
        except Exception as e:
            logger.error(f"Error getting similar items: {e}")
            return []
    
    def get_order_items(self, order_id: str) -> List[str]:
        """Get items for a specific order"""
        try:
            return self.order_items.get(order_id, [])
        except Exception as e:
            logger.error(f"Error getting order items: {e}")
            return []
    
    def generate_summary_stats(self) -> Dict:
        """Generate summary statistics"""
        try:
            total_orders = len(self.order_items)
            total_items = len(self.item_frequency)
            total_pairs = len(self.df)
            
            # Order size distribution
            order_sizes = [len(items) for items in self.order_items.values()]
            avg_order_size = np.mean(order_sizes) if order_sizes else 0
            max_order_size = max(order_sizes) if order_sizes else 0
            
            # Item frequency distribution
            item_frequencies = list(self.item_frequency.values())
            avg_item_frequency = np.mean(item_frequencies) if item_frequencies else 0
            max_item_frequency = max(item_frequencies) if item_frequencies else 0
            
            stats = {
                "total_orders": total_orders,
                "total_items": total_items,
                "total_pairs": total_pairs,
                "avg_order_size": round(avg_order_size, 2),
                "max_order_size": max_order_size,
                "avg_item_frequency": round(avg_item_frequency, 2),
                "max_item_frequency": max_item_frequency
            }
            
            # Log final summary
            self.audit_logger.log_data_quality_metrics(stats)
            self.audit_logger.end_processing()
            
            return stats
        except Exception as e:
            logger.error(f"Error generating summary stats: {e}")
            self.audit_logger.log_record_error({"operation": "summary_stats"}, str(e))
            return {}
    
    def save_audit_report(self, filename: str = None):
        """Save audit report"""
        return self.audit_logger.save_audit_report(filename)

def main():
    """Main function to test data processing"""
    processor = DataProcessor("new_orders.csv")
    
    try:
        # Load and process data
        df = processor.load_data()
        processor.build_cooccurrence_matrix()
        
        # Generate summary
        stats = processor.generate_summary_stats()
        print("Summary Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test some operations
        print("\nTop 10 Popular Items:")
        popular = processor.get_popular_items(10)
        for i, (item, freq) in enumerate(popular, 1):
            print(f"  {i}. {item}: {freq}")
        
        # Test similar items for a popular item
        if popular:
            test_item = popular[0][0]
            print(f"\nItems similar to '{test_item}':")
            similar = processor.get_similar_items(test_item, 5)
            for item, cooccurrence in similar:
                print(f"  {item}: {cooccurrence}")
        
        # Save audit report
        audit_file = processor.save_audit_report()
        print(f"\nAudit report saved to: {audit_file}")
        
    except Exception as e:
        print(f"Error in main processing: {e}")
        # Still try to save audit report even if processing failed
        try:
            audit_file = processor.save_audit_report()
            print(f"Audit report saved to: {audit_file}")
        except:
            pass

if __name__ == "__main__":
    main()
