"""
Integration module to connect the MetricsTrackingService with the existing DeltaService.
"""
import logging
from typing import Dict, Any, Optional

from src.services.youtube.base_service import BaseService
from src.services.youtube.delta_service import DeltaService
from .metrics_tracking_service import MetricsTrackingService

class MetricsDeltaIntegration(BaseService):
    """
    Integration service that connects the MetricsTrackingService with the DeltaService.
    Provides methods to analyze delta data using the metrics tracking service.
    """
    
    def __init__(self, delta_service=None, metrics_service=None, **kwargs):
        """Initialize the integration service.
        
        Args:
            delta_service: DeltaService instance
            metrics_service: MetricsTrackingService instance
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.delta_service = delta_service
        self.metrics_service = metrics_service
        
        # If services are not provided, create them
        if self.delta_service is None:
            self.delta_service = DeltaService()
            
        if self.metrics_service is None:
            self.metrics_service = MetricsTrackingService()
    
    def process_delta_with_trend_analysis(self, channel_data: Dict[str, Any],
                                        original_data: Dict[str, Any],
                                        options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process delta analysis and enhance it with trend analysis.
        
        Args:
            channel_data: Current channel data
            original_data: Original channel data for comparison
            options: Additional options for delta calculation
            
        Returns:
            Enhanced channel data with delta and trend analysis
        """
        # First, calculate standard delta using the DeltaService
        channel_with_delta = self.delta_service.calculate_deltas(
            channel_data, original_data, options
        )
        
        # Get channel ID
        channel_id = channel_data.get('channel_id')
        if not channel_id:
            logging.warning("Cannot perform trend analysis without channel_id")
            return channel_with_delta
            
        # Enhanced options for trend analysis
        trend_options = options.copy() if options else {}
        include_trend_metrics = trend_options.get('include_trend_metrics', True)
        
        if not include_trend_metrics:
            return channel_with_delta
            
        # Add trend analysis for key metrics
        metrics_to_analyze = ['subscribers', 'views', 'total_videos']
        time_window = trend_options.get('trend_time_window', 90)  # Default to 90 days
        
        # Create container for trend data
        channel_with_delta['trend_analysis'] = {}
        
        # Analyze each metric
        for metric in metrics_to_analyze:
            if metric in channel_data:
                try:
                    trend_data = self.metrics_service.analyze_historical_trends(
                        entity_id=channel_id,
                        metric_name=metric,
                        entity_type='channel',
                        time_window=time_window,
                        analysis_types=['linear_trend', 'growth_rate']
                    )
                    
                    if trend_data['status'] == 'success':
                        channel_with_delta['trend_analysis'][metric] = trend_data
                except Exception as e:
                    logging.error(f"Error analyzing trends for {metric}: {str(e)}")
                    
        # Check for threshold violations
        self._check_for_threshold_violations(channel_with_delta)
        
        return channel_with_delta
        
    def enhance_delta_report_with_trends(self, delta_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance an existing delta report with trend analysis.
        
        Args:
            delta_report: Existing delta report
            
        Returns:
            Enhanced delta report with trend analysis
        """
        # Verify this is a delta report
        if not delta_report or 'delta' not in delta_report:
            logging.warning("Cannot enhance report: not a valid delta report")
            return delta_report
            
        # Get channel ID
        channel_id = delta_report.get('channel_id')
        if not channel_id:
            logging.warning("Cannot enhance report without channel_id")
            return delta_report
            
        # Clone the report to avoid modifying the original
        enhanced_report = {**delta_report}
        
        # Add trend analysis for key metrics with changes
        delta = delta_report.get('delta', {})
        metrics_to_analyze = []
        
        # Check which metrics have changes
        for key in delta:
            if key in ['subscribers', 'views', 'total_videos']:
                metrics_to_analyze.append(key)
                
        if not metrics_to_analyze:
            # No relevant metrics to analyze
            return enhanced_report
            
        # Create container for trend data
        enhanced_report['trend_analysis'] = {}
        
        # Analyze each metric
        for metric in metrics_to_analyze:
            try:
                trend_data = self.metrics_service.analyze_historical_trends(
                    entity_id=channel_id,
                    metric_name=metric,
                    entity_type='channel',
                    time_window=90,  # Default to 90 days
                    analysis_types=['linear_trend', 'growth_rate']
                )
                
                if trend_data['status'] == 'success':
                    enhanced_report['trend_analysis'][metric] = trend_data
            except Exception as e:
                logging.error(f"Error analyzing trends for {metric}: {str(e)}")
                
        return enhanced_report
        
    def _check_for_threshold_violations(self, channel_data: Dict[str, Any]) -> None:
        """
        Check for threshold violations in trend data and add alerts.
        
        Args:
            channel_data: Channel data with trend analysis
        """
        if 'trend_analysis' not in channel_data:
            return
            
        violations_found = False
        
        for metric, trend_data in channel_data['trend_analysis'].items():
            # Check for threshold violations in the trend data
            violations = self.metrics_service.check_threshold_violations(
                entity_id=channel_data.get('channel_id', ''),
                entity_type='channel',
                metric_name=metric,
                analysis_results=trend_data
            )
            
            if violations:
                trend_data['threshold_violations'] = violations
                violations_found = True
                
        # Add overall alert flag if violations found
        if violations_found:
            channel_data['has_threshold_violations'] = True
