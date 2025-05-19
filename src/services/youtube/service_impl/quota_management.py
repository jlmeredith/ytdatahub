"""
Quota management functionality for the YouTube service implementation.
"""

class QuotaManagementMixin:
    """
    Mixin class providing quota management functionality for the YouTube service.
    """
    
    def track_quota_usage(self, operation):
        """
        Track quota usage for a specific API operation.
        
        Args:
            operation (str): API operation name (e.g., 'channels.list')
            
        Returns:
            int: Quota cost for the operation
        """
        # Update internal attribute for backward compatibility
        cost = self.quota_service.track_quota_usage(operation)
        self._quota_used = self.quota_service._quota_used
        return cost
        
    def get_current_quota_usage(self):
        """
        Get the current cumulative quota usage.
        
        Returns:
            int: Total quota used so far
        """
        self._quota_used = self.quota_service._quota_used
        return self._quota_used
        
    def get_remaining_quota(self):
        """
        Get the remaining available quota.
        
        Returns:
            int: Remaining quota available
        """
        return self.quota_service.get_remaining_quota()
    
    def use_quota(self, amount):
        """
        Use a specific amount of quota and check if we exceed the limit.
        
        Args:
            amount (int): Amount of quota to use
            
        Raises:
            ValueError: If using this amount would exceed the quota limit
        """
        self.quota_service.use_quota(amount)
        self._quota_used = self.quota_service._quota_used
    
    def estimate_quota_usage(self, options, video_count=None):
        """
        Estimate YouTube API quota usage for given options.
        
        Args:
            options (dict): Collection options
            video_count (int, optional): Number of videos if known
            
        Returns:
            int: Estimated quota usage
        """
        return self.quota_service.estimate_quota_usage(options, video_count)
