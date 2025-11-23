"""
Individual Luigi tasks for the campaign pipeline.

Each task represents a discrete step in the video generation workflow.
"""

import luigi
import logging
import asyncio
from typing import Dict, Any, List, Tuple, Optional

from .base import AsyncCampaignTask, CampaignPipelineTask

logger = logging.getLogger(__name__)


class AssetCollectionTask(AsyncCampaignTask):
    """
    Task 1: Collect all image assets for the campaign.

    Fetches all image assets associated with the campaign from the database.
    """

    async def async_run(self) -> Dict[str, Any]:
        """Fetch campaign assets."""
        from ..database_helpers import list_assets

        logger.info(f"Collecting assets for campaign {self.campaign_id}")

        assets = list_assets(
            user_id=None,
            campaign_id=self.campaign_id,
            asset_type="image",
            limit=1000,
            offset=0,
        )

        logger.info(f"Found {len(assets)} image assets for campaign {self.campaign_id}")

        if len(assets) < 2:
            raise ValueError(
                f"Need at least 2 image assets, but campaign has {len(assets)}"
            )

        # Store asset IDs for next tasks
        asset_ids = [asset.id for asset in assets]

        return {
            "asset_count": len(assets),
            "asset_ids": asset_ids,
        }


class ImagePairSelectionTask(AsyncCampaignTask):
    """
    Task 2: Use xAI Grok to select optimal image pairs.

    Analyzes campaign assets and selects pairs that will create compelling videos.
    """

    num_pairs = luigi.IntParameter(default=10, description="Target number of pairs")

    def requires(self):
        """Depends on asset collection."""
        return AssetCollectionTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    async def async_run(self) -> Dict[str, Any]:
        """Select image pairs using xAI Grok."""
        from ..services.xai_client import XAIClient
        from ..database_helpers import (
            list_assets,
            get_campaign_by_id,
            get_client_by_id,
        )

        logger.info(f"Selecting image pairs for campaign {self.campaign_id}")

        self.update_job_status("image_pair_selection")

        # Get assets
        assets = list_assets(
            user_id=None,
            campaign_id=self.campaign_id,
            asset_type="image",
            limit=1000,
            offset=0,
        )

        # Prepare asset data for Grok
        import json

        asset_data = []
        for asset in assets:
            tags = getattr(asset, "tags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            elif tags is None:
                tags = []

            asset_dict = {
                "id": asset.id,
                "name": getattr(asset, "name", ""),
                "description": getattr(asset, "name", ""),
                "tags": tags,
                "type": "image",
                "url": getattr(asset, "url", ""),
            }
            asset_data.append(asset_dict)

        # Get campaign context
        campaign = get_campaign_by_id(self.campaign_id, None)
        campaign_context = None
        if campaign:
            campaign_context = {
                "goal": campaign.get("goal"),
                "name": campaign.get("name"),
            }

        # Get client brand guidelines
        brand_guidelines = None
        if campaign and campaign.get("clientId"):
            client = get_client_by_id(campaign["clientId"], None)
            if client and client.get("brandGuidelines"):
                brand_guidelines = client["brandGuidelines"]

        # Select pairs using Grok
        xai_client = XAIClient()
        image_pairs = xai_client.select_image_pairs(
            assets=asset_data,
            campaign_context=campaign_context,
            client_brand_guidelines=brand_guidelines,
            num_pairs=self.num_pairs,
        )

        logger.info(f"Selected {len(image_pairs)} image pairs")

        # Store pairs for next tasks
        pairs_data = [
            {
                "image1_id": pair[0],
                "image2_id": pair[1],
                "score": pair[2],
                "reasoning": pair[3],
            }
            for pair in image_pairs
        ]

        return {
            "pairs_count": len(image_pairs),
            "pairs": pairs_data,
        }


class SubJobCreationTask(CampaignPipelineTask):
    """
    Task 3: Create sub-jobs for each image pair.

    Creates database records for each video generation sub-job.
    """

    clip_duration = luigi.FloatParameter(default=6.0, description="Clip duration in seconds")

    def requires(self):
        """Depends on image pair selection."""
        return ImagePairSelectionTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    def run(self):
        """Create sub-jobs in database."""
        from ..database import create_sub_job
        from ..services.scene_prompts import get_scene_prompt
        from ..config import get_settings

        self.log_task_start()

        try:
            # Get selected pairs from previous task
            pairs_data = self.input().get_output_data()
            pairs = pairs_data["pairs"]

            logger.info(f"Creating {len(pairs)} sub-jobs for job {self.job_id}")

            self.update_job_status("sub_job_creation")

            settings = get_settings()
            video_model = settings.VIDEO_GENERATION_MODEL

            # Round duration for Veo3
            from ..services.sub_job_orchestrator import _round_duration_for_veo3
            rounded_duration = _round_duration_for_veo3(self.clip_duration)

            sub_job_ids = []
            for i, pair in enumerate(pairs, 1):
                # Get scene-specific prompt
                scene_info = get_scene_prompt(i if i <= 7 else ((i - 1) % 7) + 1)

                sub_job_id = create_sub_job(
                    job_id=self.job_id,
                    sub_job_number=i,
                    image1_asset_id=pair["image1_id"],
                    image2_asset_id=pair["image2_id"],
                    model_id=video_model,
                    input_parameters={
                        "duration": rounded_duration or scene_info["duration"],
                        "score": pair["score"],
                        "reasoning": pair["reasoning"],
                        "prompt": scene_info["prompt"],
                        "scene_number": scene_info["scene_number"],
                        "scene_name": scene_info["name"],
                        "motion_goal": scene_info["motion_goal"],
                    },
                )
                sub_job_ids.append(sub_job_id)

            logger.info(f"Created {len(sub_job_ids)} sub-jobs")

            # Mark complete
            self.mark_complete({
                "sub_job_count": len(sub_job_ids),
                "sub_job_ids": sub_job_ids,
                "rounded_duration": rounded_duration,
            })

        except Exception as e:
            self.log_task_failure(e)
            raise


class VideoGenerationSubTask(AsyncCampaignTask):
    """
    Sub-task for generating a single video from an image pair.

    This task is created dynamically for each sub-job.
    """

    sub_job_id = luigi.Parameter(description="Sub-job ID")
    clip_duration = luigi.FloatParameter(default=6.0)

    async def async_run(self) -> Dict[str, Any]:
        """Generate video for this image pair."""
        from ..database import get_sub_job_by_id, update_sub_job_status
        from ..database_helpers import get_asset_by_id
        from ..services.replicate_client import ReplicateClient
        from ..config import get_settings
        from ..auth import create_asset_access_token

        logger.info(f"Generating video for sub-job {self.sub_job_id}")

        # Get sub-job details
        sub_job = get_sub_job_by_id(self.sub_job_id)
        if not sub_job:
            raise ValueError(f"Sub-job {self.sub_job_id} not found")

        # Get asset URLs
        image1 = get_asset_by_id(sub_job["image1AssetId"])
        image2 = get_asset_by_id(sub_job["image2AssetId"])

        if not image1 or not image2:
            raise ValueError(f"Assets not found for sub-job {self.sub_job_id}")

        # Construct asset URLs
        settings = get_settings()
        external_url = settings.NGROK_URL or settings.BASE_URL

        # Generate access tokens
        image1_token = create_asset_access_token(sub_job["image1AssetId"])
        image2_token = create_asset_access_token(sub_job["image2AssetId"])

        # Use source URL if available
        if hasattr(image1, 'source_url') and image1.source_url:
            image1_url = image1.source_url
        else:
            base_url = f"{external_url}{image1.url}" if not image1.url.startswith('http') else image1.url
            image1_url = f"{base_url}?token={image1_token}"

        if hasattr(image2, 'source_url') and image2.source_url:
            image2_url = image2.source_url
        else:
            base_url = f"{external_url}{image2.url}" if not image2.url.startswith('http') else image2.url
            image2_url = f"{base_url}?token={image2_token}"

        # Update status
        update_sub_job_status(self.sub_job_id, "processing")

        # Get scene prompt
        input_params = sub_job.get("inputParameters", {})
        scene_prompt = input_params.get("prompt") or input_params.get("scene_prompt")

        # Generate video
        replicate_client = ReplicateClient()
        result = await asyncio.to_thread(
            replicate_client.generate_video_from_pair,
            image1_url,
            image2_url,
            model=sub_job["modelId"],
            duration=self.clip_duration,
            prompt=scene_prompt,
        )

        if not result["success"]:
            update_sub_job_status(
                self.sub_job_id,
                "failed",
                error_message=result.get("error", "Unknown error"),
            )
            raise Exception(result.get("error", "Video generation failed"))

        # Download video
        from ..services.sub_job_orchestrator import _download_video

        video_url = result["video_url"]
        clip_path = await _download_video(
            self.job_id,
            sub_job["subJobNumber"],
            video_url
        )

        # Calculate cost
        duration = result.get("duration_seconds", self.clip_duration or 6)
        if sub_job["modelId"] == "veo3":
            cost = duration * ReplicateClient.VEO3_PRICE_PER_SECOND
        else:
            cost = ReplicateClient.HAILUO2_PRICE_PER_GENERATION

        # Update as completed
        update_sub_job_status(
            self.sub_job_id,
            "completed",
            replicate_prediction_id=result.get("prediction_id"),
            video_url=video_url,
            duration_seconds=duration,
            actual_cost=cost,
            progress=1.0,
        )

        logger.info(f"Sub-job {self.sub_job_id} completed successfully")

        return {
            "clip_path": clip_path,
            "video_url": video_url,
            "cost": cost,
            "duration": duration,
        }


class ParallelVideoGenerationTask(CampaignPipelineTask):
    """
    Task 4: Launch all video generation sub-tasks in parallel.

    This is a wrapper task that depends on all sub-tasks completing.
    """

    clip_duration = luigi.FloatParameter(default=6.0)

    def requires(self):
        """
        Depends on all sub-job generation tasks.

        Returns a list of VideoGenerationSubTask instances.
        """
        # Get sub-job IDs from previous task
        sub_jobs_output = SubJobCreationTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id,
            clip_duration=self.clip_duration
        ).output().get_output_data()

        if not sub_jobs_output:
            raise ValueError("Sub-jobs not created yet")

        sub_job_ids = sub_jobs_output["sub_job_ids"]
        rounded_duration = sub_jobs_output.get("rounded_duration", self.clip_duration)

        # Create a task for each sub-job
        return [
            VideoGenerationSubTask(
                job_id=self.job_id,
                campaign_id=self.campaign_id,
                sub_job_id=sub_job_id,
                clip_duration=rounded_duration
            )
            for sub_job_id in sub_job_ids
        ]

    def run(self):
        """Aggregate results from all sub-tasks."""
        self.log_task_start()

        try:
            self.update_job_status("sub_job_processing")

            # Get results from all sub-tasks
            sub_task_results = []
            for sub_task in self.requires():
                result = sub_task.get_output_data()
                if result:
                    sub_task_results.append(result)

            successful = [r for r in sub_task_results if r.get("clip_path")]
            failed = len(sub_task_results) - len(successful)

            logger.info(f"Video generation complete: {len(successful)} succeeded, {failed} failed")

            if not successful:
                raise Exception("All sub-jobs failed")

            # Mark complete with aggregated results
            self.mark_complete({
                "total_clips": len(sub_task_results),
                "successful_clips": len(successful),
                "failed_clips": failed,
                "clip_paths": [r["clip_path"] for r in successful],
                "clip_urls": [r["video_url"] for r in successful],
                "total_cost": sum(r.get("cost", 0.0) for r in successful),
            })

        except Exception as e:
            self.log_task_failure(e)
            raise


class AudioGenerationTask(AsyncCampaignTask):
    """
    Task 5: Generate background music for the video.
    """

    def requires(self):
        """Depends on video generation completing."""
        return ParallelVideoGenerationTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    async def async_run(self) -> Dict[str, Any]:
        """Generate progressive audio."""
        from ..services.musicgen_client import MusicGenClient
        from ..services.scene_prompts import get_all_scenes
        import tempfile
        from pathlib import Path
        import requests

        logger.info(f"Generating audio for job {self.job_id}")

        self.update_job_status("audio_generation")

        # Get clip count from previous task
        video_results = self.input().get_output_data()
        num_scenes = video_results["successful_clips"]

        # Get scene prompts
        all_scenes = get_all_scenes()
        scene_prompts = []
        for i in range(num_scenes):
            scene_index = i % len(all_scenes)
            scene_prompts.append(all_scenes[scene_index])

        # Generate audio
        musicgen_client = MusicGenClient()
        result = await asyncio.to_thread(
            musicgen_client.generate_progressive_audio,
            scene_prompts,
            duration_per_scene=4,
        )

        if not result["success"]:
            logger.warning(f"Audio generation failed: {result['error']}")
            return {"audio_generated": False, "error": result["error"]}

        # Download audio
        audio_url = result["final_audio_url"]
        temp_dir = Path(tempfile.gettempdir()) / f"job_{self.job_id}"
        temp_dir.mkdir(exist_ok=True)
        audio_path = temp_dir / "background_music.mp3"

        response = await asyncio.to_thread(
            requests.get, audio_url, stream=True, timeout=300
        )
        response.raise_for_status()

        with open(audio_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Audio downloaded to {audio_path}")

        return {
            "audio_generated": True,
            "audio_path": str(audio_path),
            "audio_url": audio_url,
        }


class VideoCombinationTask(AsyncCampaignTask):
    """
    Task 6: Combine all video clips into one video.
    """

    def requires(self):
        """Depends on video generation."""
        return ParallelVideoGenerationTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    async def async_run(self) -> Dict[str, Any]:
        """Combine video clips."""
        from ..services.video_combiner import combine_video_clips
        from pathlib import Path
        import tempfile

        logger.info(f"Combining clips for job {self.job_id}")

        self.update_job_status("video_combining")

        # Get clip paths
        video_results = self.input().get_output_data()
        clip_paths = video_results["clip_paths"]

        # Create output path
        temp_dir = Path(tempfile.gettempdir()) / f"job_{self.job_id}"
        combined_path = temp_dir / "combined.mp4"

        # Combine videos
        success, output_path, metadata = await asyncio.to_thread(
            combine_video_clips,
            clip_paths,
            str(combined_path),
            transition_duration=0.0,
            output_resolution="1920x1080",
            output_fps=30,
            keep_audio=False,
        )

        if not success:
            raise Exception("Failed to combine video clips")

        logger.info(f"Combined video created at {output_path}")

        return {
            "combined_path": output_path,
            "metadata": metadata,
        }


class AudioMergingTask(AsyncCampaignTask):
    """
    Task 7: Merge audio with combined video.
    """

    def requires(self):
        """Depends on both video combination and audio generation."""
        return {
            "video": VideoCombinationTask(
                job_id=self.job_id,
                campaign_id=self.campaign_id
            ),
            "audio": AudioGenerationTask(
                job_id=self.job_id,
                campaign_id=self.campaign_id
            ),
        }

    async def async_run(self) -> Dict[str, Any]:
        """Merge audio with video."""
        from ..services.video_combiner import add_audio_to_video
        from pathlib import Path
        import tempfile

        logger.info(f"Merging audio for job {self.job_id}")

        # Get inputs
        video_result = self.input()["video"].get_output_data()
        audio_result = self.input()["audio"].get_output_data()

        combined_path = video_result["combined_path"]

        # Check if audio was generated
        if not audio_result.get("audio_generated"):
            logger.warning("No audio generated, skipping merge")
            return {
                "final_path": combined_path,
                "audio_merged": False,
            }

        audio_path = audio_result["audio_path"]

        # Merge
        temp_dir = Path(tempfile.gettempdir()) / f"job_{self.job_id}"
        final_path = temp_dir / "final_with_audio.mp4"

        success, output_path, error = await asyncio.to_thread(
            add_audio_to_video,
            combined_path,
            audio_path,
            str(final_path),
            audio_fade_duration=0.5,
        )

        if not success:
            logger.warning(f"Failed to merge audio: {error}, using video without audio")
            return {
                "final_path": combined_path,
                "audio_merged": False,
            }

        logger.info(f"Audio merged successfully: {output_path}")

        return {
            "final_path": output_path,
            "audio_merged": True,
        }


class VideoStorageTask(AsyncCampaignTask):
    """
    Task 8: Store final video in database.

    This is the final task in the pipeline.
    """

    def requires(self):
        """Depends on audio merging."""
        return AudioMergingTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

    async def async_run(self) -> Dict[str, Any]:
        """Store final video in database."""
        from ..database import get_db

        logger.info(f"Storing final video for job {self.job_id}")

        # Get final video path
        merge_result = self.input().get_output_data()
        final_path = merge_result["final_path"]

        # Read video file
        with open(final_path, 'rb') as f:
            video_data = f.read()

        # Store in database
        with get_db() as conn:
            conn.execute(
                """
                UPDATE generated_videos
                SET video_data = ?
                WHERE id = ?
                """,
                (video_data, self.job_id)
            )
            conn.commit()

        combined_url = f"/api/v3/videos/{self.job_id}/combined"

        logger.info(f"Stored final video (size={len(video_data)} bytes)")

        # Update job status to completed
        self.update_job_status("completed", video_url=combined_url)

        return {
            "video_url": combined_url,
            "video_size": len(video_data),
        }
