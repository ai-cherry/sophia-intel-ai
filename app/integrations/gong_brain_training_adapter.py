#!/usr/bin/env python3
"""
Gong Brain Training Adapter
Connects Gong CSV ingestion with Sophia's Brain Training Pipeline
Enables learning from Gong sales data through the brain training UI
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.integrations.gong_csv_ingestion import GongCSVIngestionPipeline, GongCSVRecord
from app.swarms.knowledge.brain_training import BrainTrainingPipeline, ContentIngestionResult

logger = logging.getLogger(__name__)


class GongBrainTrainingAdapter:
    """
    Adapter that connects Gong data ingestion with Sophia's Brain Training Pipeline
    This allows Gong CSV exports to be processed through the sophisticated learning system
    """

    def __init__(
        self, memory_system, brain_training_pipeline: Optional[BrainTrainingPipeline] = None
    ):
        """
        Initialize the adapter

        Args:
            memory_system: The memory system for storing learned content
            brain_training_pipeline: Existing brain training pipeline or create new one
        """
        self.memory_system = memory_system

        # Initialize brain training pipeline if not provided
        if brain_training_pipeline:
            self.brain_training = brain_training_pipeline
        else:
            self.brain_training = BrainTrainingPipeline(
                memory_system=memory_system,
                config={
                    "meta_learning_enabled": True,
                    "reinforcement_learning_enabled": True,
                    "adaptive_learning_rate": True,
                },
            )

        # Initialize Gong CSV pipeline
        self.gong_csv_pipeline = GongCSVIngestionPipeline()

        # Training statistics
        self.training_stats = {
            "total_calls_trained": 0,
            "total_transcripts_processed": 0,
            "concepts_extracted": 0,
            "sales_patterns_identified": 0,
            "objection_handlers_learned": 0,
            "success_stories_captured": 0,
        }

        logger.info("Gong Brain Training Adapter initialized")

    async def train_from_gong_csv(
        self, csv_path: str, learning_objectives: list[str] = None
    ) -> dict[str, Any]:
        """
        Train Sophia's brain using Gong CSV data

        Args:
            csv_path: Path to Gong CSV export file
            learning_objectives: Specific learning goals for this training

        Returns:
            Training results and statistics
        """
        logger.info(f"Starting Gong brain training from: {csv_path}")

        # Set default learning objectives for sales data
        if not learning_objectives:
            learning_objectives = [
                "Learn effective sales conversation patterns",
                "Identify common customer objections and responses",
                "Extract successful closing techniques",
                "Understand product positioning strategies",
                "Recognize buying signals and customer intent",
            ]

        # Start a training session
        session_id = await self.brain_training.start_training_session(
            objectives=learning_objectives, sources=[csv_path]
        )

        try:
            # Process CSV file to extract Gong records
            csv_stats = self.gong_csv_pipeline.process_csv_file(
                csv_path=csv_path, format_type="auto"
            )

            logger.info(f"CSV processing stats: {csv_stats}")

            # Read the CSV to get actual records for brain training
            df = pd.read_csv(csv_path)
            records = self._extract_gong_records(df)

            # Train on each call record
            training_results = []
            for record in records:
                result = await self._train_on_call_record(record)
                training_results.append(result)
                self.training_stats["total_calls_trained"] += 1

            # Extract sales-specific insights
            sales_insights = await self._extract_sales_insights(records)

            # Incorporate sales patterns into learning
            for insight in sales_insights:
                await self.brain_training.train_custom_response(
                    query=insight["pattern_query"],
                    desired_response=insight["pattern_response"],
                    context={"source": "gong_sales_data", "type": insight["pattern_type"]},
                )

            # End training session
            session_summary = await self.brain_training.end_training_session()

            # Generate comprehensive report
            report = {
                "session_id": session_id,
                "csv_file": csv_path,
                "records_processed": len(records),
                "training_results": {
                    "successful_trainings": len([r for r in training_results if r.success]),
                    "failed_trainings": len([r for r in training_results if not r.success]),
                    "total_fragments_created": sum(r.fragments_created for r in training_results),
                    "total_concepts_identified": sum(
                        r.concepts_identified for r in training_results
                    ),
                },
                "sales_insights": {
                    "patterns_identified": len(sales_insights),
                    "objection_handlers": self.training_stats["objection_handlers_learned"],
                    "success_stories": self.training_stats["success_stories_captured"],
                },
                "session_summary": session_summary,
                "learning_objectives_progress": await self._get_objectives_progress(
                    learning_objectives
                ),
            }

            logger.info(f"Gong brain training completed: {report}")
            return report

        except Exception as e:
            logger.error(f"Error in Gong brain training: {e}")
            await self.brain_training.end_training_session()
            raise

    async def train_from_directory(self, directory_path: str) -> dict[str, Any]:
        """
        Train from all Gong CSV files in a directory

        Args:
            directory_path: Path to directory containing Gong CSV exports

        Returns:
            Combined training results
        """
        csv_files = list(Path(directory_path).glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files for training")

        all_results = []
        for csv_file in csv_files:
            try:
                result = await self.train_from_gong_csv(str(csv_file))
                all_results.append(result)
            except Exception as e:
                logger.error(f"Failed to train from {csv_file}: {e}")

        return {
            "files_processed": len(all_results),
            "total_records": sum(r["records_processed"] for r in all_results),
            "total_concepts": sum(
                r["training_results"]["total_concepts_identified"] for r in all_results
            ),
            "individual_results": all_results,
        }

    async def apply_user_feedback(self, feedback: dict[str, Any]) -> dict[str, Any]:
        """
        Apply user feedback about Gong data training

        Args:
            feedback: User feedback about training quality

        Returns:
            Feedback incorporation results
        """
        # Format feedback for brain training pipeline
        feedback_record = {
            "timestamp": datetime.now().isoformat(),
            "source": "gong_training_feedback",
            "feedback": feedback,
        }

        # Incorporate feedback
        result = await self.brain_training.incorporate_feedback(feedback_record)

        # Update training strategies based on feedback
        if feedback.get("improve_objection_handling"):
            await self._improve_objection_pattern_learning()

        if feedback.get("focus_on_closing_techniques"):
            await self._enhance_closing_pattern_recognition()

        return result

    async def query_learned_sales_knowledge(self, query: str) -> dict[str, Any]:
        """
        Query the learned sales knowledge from Gong training

        Args:
            query: Question about sales patterns or specific calls

        Returns:
            Answer based on learned Gong data
        """
        # Search through learned content
        search_results = await self.memory_system.search(
            query=query, filters={"source": "gong_training"}, limit=5
        )

        # Generate response based on learned patterns
        if search_results:
            response = await self._generate_sales_insight_response(query, search_results)
        else:
            response = {
                "answer": "No relevant sales data found for this query.",
                "confidence": 0.0,
                "sources": [],
            }

        return response

    # Private helper methods

    def _extract_gong_records(self, df: pd.DataFrame) -> list[GongCSVRecord]:
        """Extract Gong records from DataFrame"""
        records = []

        # Normalize column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        for _, row in df.iterrows():
            # Create GongCSVRecord from row data
            record = GongCSVRecord(
                call_id=str(row.get("call_id", row.get("id", ""))),
                title=row.get("title", row.get("call_title", "Unknown")),
                date=str(row.get("date", row.get("scheduled", ""))),
                duration=int(row.get("duration", 0) or 0),
                participants=self._parse_participants_from_row(row),
                transcript=row.get("transcript", row.get("notes", "")),
                account_name=row.get("account", row.get("account_name", "")),
                deal_stage=row.get("deal_stage", ""),
                call_outcome=row.get("outcome", ""),
            )

            if record.transcript:  # Only include records with content
                records.append(record)

        return records

    def _parse_participants_from_row(self, row) -> list[str]:
        """Parse participants from DataFrame row"""
        participants = []

        for col in ["participants", "attendees", "speakers"]:
            if col in row and pd.notna(row[col]):
                value = str(row[col])
                if value:
                    participants.extend([p.strip() for p in value.split(",")])

        return list(set(participants))  # Remove duplicates

    async def _train_on_call_record(self, record: GongCSVRecord) -> ContentIngestionResult:
        """Train on a single call record"""
        # Format record as training content
        content = {
            "type": "gong_call",
            "call_id": record.call_id,
            "title": record.title,
            "transcript": record.transcript,
            "metadata": {
                "date": record.date,
                "duration": record.duration,
                "participants": record.participants,
                "account": record.account_name,
                "deal_stage": record.deal_stage,
                "outcome": record.call_outcome,
            },
        }

        # Ingest through brain training pipeline
        result = await self.brain_training.ingest_content(content)

        # Update transcript counter
        if result.success and record.transcript:
            self.training_stats["total_transcripts_processed"] += 1
            self.training_stats["concepts_extracted"] += result.concepts_identified

        return result

    async def _extract_sales_insights(self, records: list[GongCSVRecord]) -> list[dict[str, Any]]:
        """Extract sales-specific insights from Gong records"""
        insights = []

        for record in records:
            if not record.transcript:
                continue

            transcript_lower = record.transcript.lower()

            # Identify objection patterns
            if any(
                word in transcript_lower
                for word in ["concern", "worried", "expensive", "competitor"]
            ):
                insight = {
                    "pattern_type": "objection_handling",
                    "pattern_query": f"How to handle objection about {record.account_name}",
                    "pattern_response": self._extract_objection_response(record.transcript),
                    "source_call": record.call_id,
                }
                insights.append(insight)
                self.training_stats["objection_handlers_learned"] += 1

            # Identify successful closes
            if record.call_outcome and "success" in record.call_outcome.lower():
                insight = {
                    "pattern_type": "successful_close",
                    "pattern_query": f"Successful closing technique for {record.deal_stage}",
                    "pattern_response": self._extract_closing_technique(record.transcript),
                    "source_call": record.call_id,
                }
                insights.append(insight)
                self.training_stats["success_stories_captured"] += 1

            # Identify product positioning
            if any(word in transcript_lower for word in ["feature", "benefit", "value", "roi"]):
                insight = {
                    "pattern_type": "product_positioning",
                    "pattern_query": f"How to position product for {record.account_name}",
                    "pattern_response": self._extract_value_proposition(record.transcript),
                    "source_call": record.call_id,
                }
                insights.append(insight)

        self.training_stats["sales_patterns_identified"] += len(insights)
        return insights

    def _extract_objection_response(self, transcript: str) -> str:
        """Extract how objections were handled"""
        # Simple extraction - can be enhanced with NLP
        lines = transcript.split("\n")
        for i, line in enumerate(lines):
            if any(word in line.lower() for word in ["concern", "worried", "expensive"]):
                # Get the next few lines as the response
                response_lines = lines[i + 1 : i + 4]
                return " ".join(response_lines)
        return "Address the concern directly and provide value justification."

    def _extract_closing_technique(self, transcript: str) -> str:
        """Extract closing technique from successful call"""
        # Look for closing indicators
        closing_phrases = [
            "next steps",
            "move forward",
            "get started",
            "timeline",
            "implementation",
        ]

        lines = transcript.split("\n")
        for line in lines:
            if any(phrase in line.lower() for phrase in closing_phrases):
                return line

        return "Establish clear next steps and timeline for implementation."

    def _extract_value_proposition(self, transcript: str) -> str:
        """Extract value proposition statements"""
        value_keywords = ["roi", "save", "increase", "improve", "reduce", "benefit"]

        value_statements = []
        lines = transcript.split("\n")
        for line in lines:
            if any(keyword in line.lower() for keyword in value_keywords):
                value_statements.append(line)

        if value_statements:
            return " ".join(value_statements[:3])  # Top 3 value statements

        return "Focus on quantifiable benefits and ROI."

    async def _get_objectives_progress(self, objectives: list[str]) -> dict[str, float]:
        """Get progress on learning objectives"""
        progress = {}

        for objective in objectives:
            # Simplified progress tracking
            if "objection" in objective.lower():
                progress[objective] = min(
                    1.0, self.training_stats["objection_handlers_learned"] / 10
                )
            elif "closing" in objective.lower():
                progress[objective] = min(1.0, self.training_stats["success_stories_captured"] / 5)
            elif "pattern" in objective.lower():
                progress[objective] = min(
                    1.0, self.training_stats["sales_patterns_identified"] / 20
                )
            else:
                progress[objective] = 0.5  # Default progress

        return progress

    async def _improve_objection_pattern_learning(self):
        """Improve objection handling pattern recognition"""
        # Add more sophisticated objection patterns
        objection_patterns = [
            ("price objection", "Focus on value and ROI rather than cost"),
            ("competitor comparison", "Highlight unique differentiators"),
            ("implementation concern", "Provide clear timeline and support plan"),
        ]

        for pattern, response in objection_patterns:
            await self.brain_training.train_custom_response(
                query=f"How to handle {pattern}",
                desired_response=response,
                context={"type": "objection_handling", "source": "gong_feedback"},
            )

    async def _enhance_closing_pattern_recognition(self):
        """Enhance closing technique pattern recognition"""
        # Add closing technique patterns
        closing_patterns = [
            ("trial close", "Would it make sense to explore a pilot program?"),
            ("assumptive close", "When would be the best time to start implementation?"),
            ("urgency close", "This pricing is available until end of quarter"),
        ]

        for pattern, example in closing_patterns:
            await self.brain_training.train_custom_response(
                query=f"Example of {pattern}",
                desired_response=example,
                context={"type": "closing_technique", "source": "gong_feedback"},
            )

    async def _generate_sales_insight_response(
        self, query: str, search_results: list[dict]
    ) -> dict[str, Any]:
        """Generate response based on learned sales data"""
        # Compile relevant content from search results
        relevant_content = []
        sources = []

        for result in search_results:
            content = result.get("content", "")
            metadata = result.get("metadata", {})

            if content:
                relevant_content.append(content)
                sources.append(
                    {
                        "call_id": metadata.get("source", "Unknown"),
                        "relevance": result.get("similarity", 0.0),
                    }
                )

        # Generate comprehensive answer
        if relevant_content:
            answer = "Based on learned Gong sales data:\n\n"
            answer += "\n\n".join(relevant_content[:3])  # Top 3 most relevant
            confidence = sum(s["relevance"] for s in sources) / len(sources)
        else:
            answer = "No specific sales patterns found for this query."
            confidence = 0.0

        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "training_stats": self.training_stats,
        }

    async def get_training_metrics(self) -> dict[str, Any]:
        """Get comprehensive training metrics"""
        brain_metrics = await self.brain_training.get_learning_metrics()

        return {
            "gong_training_stats": self.training_stats,
            "brain_training_metrics": brain_metrics,
            "integration_health": {
                "csv_pipeline_ready": True,
                "brain_training_active": self.brain_training.current_session is not None,
                "memory_system_connected": self.memory_system is not None,
            },
        }


# Export main class
__all__ = ["GongBrainTrainingAdapter"]
