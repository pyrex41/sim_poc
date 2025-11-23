"""
Main campaign pipeline workflow.

This module defines the complete end-to-end workflow for campaign video generation.
"""

import luigi
import logging
from typing import Optional

from .tasks import (
    AssetCollectionTask,
    ImagePairSelectionTask,
    SubJobCreationTask,
    ParallelVideoGenerationTask,
    AudioGenerationTask,
    VideoCombinationTask,
    AudioMergingTask,
    VideoStorageTask,
)

logger = logging.getLogger(__name__)


class CampaignPipelineWorkflow(luigi.WrapperTask):
    """
    Complete campaign video generation workflow.

    This is the entry point for the entire pipeline. It orchestrates all
    tasks from asset collection through final video storage.

    Usage:
        # From command line
        luigi --module workflows.campaign_pipeline CampaignPipelineWorkflow \
            --job-id 123 \
            --campaign-id camp-abc \
            --local-scheduler

        # From Python code
        luigi.build([
            CampaignPipelineWorkflow(
                job_id=123,
                campaign_id="camp-abc"
            )
        ], workers=10)
    """

    job_id = luigi.IntParameter(description="Parent job ID")
    campaign_id = luigi.Parameter(description="Campaign ID")
    clip_duration = luigi.FloatParameter(
        default=6.0,
        description="Duration for each video clip in seconds"
    )
    num_pairs = luigi.IntParameter(
        default=10,
        description="Target number of image pairs to select"
    )

    def requires(self):
        """
        The final task of the pipeline.

        Luigi automatically resolves all dependencies starting from this task.
        """
        return VideoStorageTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    def complete(self):
        """
        Check if the entire workflow is complete.

        Returns True if the final task (VideoStorageTask) is complete.
        """
        return self.requires().complete()


class CampaignPipelineWorkflowWithParams(CampaignPipelineWorkflow):
    """
    Variant of the workflow that accepts additional parameters.

    Use this when you want more control over the pipeline configuration.
    """

    skip_audio = luigi.BoolParameter(
        default=False,
        description="Skip audio generation and merging"
    )

    def requires(self):
        """
        Conditionally skip audio-related tasks.
        """
        if self.skip_audio:
            # Skip audio tasks, go straight to storage after combination
            return VideoCombinationTask(
                job_id=self.job_id,
                campaign_id=self.campaign_id
            )
        else:
            # Normal flow with audio
            return super().requires()


class PropertyVideoPipelineWorkflow(luigi.WrapperTask):
    """
    Specialized workflow for property video generation.

    This workflow is optimized for luxury lodging properties with
    predefined scene types.
    """

    job_id = luigi.IntParameter()
    campaign_id = luigi.Parameter()
    property_name = luigi.Parameter()
    clip_duration = luigi.FloatParameter(default=6.0)

    def requires(self):
        """
        Property videos use the same pipeline but with different parameters.
        """
        return VideoStorageTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    def complete(self):
        """Check if the workflow is complete."""
        return self.requires().complete()


# Export all workflow classes
__all__ = [
    "CampaignPipelineWorkflow",
    "CampaignPipelineWorkflowWithParams",
    "PropertyVideoPipelineWorkflow",
]
