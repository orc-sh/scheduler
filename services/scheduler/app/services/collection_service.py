"""
Collection service for executing collections on API endpoints.
"""

import asyncio
import json
import statistics
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.models.collection_reports import CollectionReport
from app.models.collection_results import CollectionResult
from app.models.collection_runs import CollectionRun
from app.models.collections import Collection
from app.services.webhook_service import get_webhook_service


class CollectionService:
    """Service class for collection operations"""

    def __init__(self, db: Session):
        """
        Initialize the collection service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_collection(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Collection:
        """
        Create a new collection.

        Args:
            project_id: ID of the project
            name: Collection name (optional)
            description: Collection description (optional)

        Returns:
            Created Collection instance
        """
        collection = Collection(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=name,
            description=description,
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """
        Get a collection by ID.

        Args:
            collection_id: ID of the collection

        Returns:
            Collection instance if found, None otherwise
        """
        return self.db.query(Collection).filter(Collection.id == collection_id).first()

    def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Collection]:
        """
        Update a collection's properties.

        Args:
            collection_id: ID of the collection to update
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated Collection instance if found, None otherwise
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return None

        # Update fields if provided
        if name is not None:
            collection.name = name  # type: ignore[assignment]
        if description is not None:
            collection.description = description  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(collection)
        return collection

    def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection and all its runs.

        Args:
            collection_id: ID of the collection to delete

        Returns:
            True if collection was deleted, False if not found
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return False

        self.db.delete(collection)
        self.db.commit()
        return True

    def create_collection_run(
        self,
        collection_id: str,
        concurrent_users: int = 10,
        duration_seconds: int = 60,
        requests_per_second: Optional[int] = None,
    ) -> CollectionRun:
        """
        Create a new collection run from a collection.

        Args:
            collection_id: ID of the webhook collection
            concurrent_users: Number of concurrent users
            duration_seconds: Duration in seconds
            requests_per_second: Optional rate limit

        Returns:
            Created CollectionRun instance
        """
        collection_run = CollectionRun(
            id=str(uuid.uuid4()),
            collection_id=collection_id,
            status="pending",
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            requests_per_second=requests_per_second,
        )
        self.db.add(collection_run)
        self.db.commit()
        self.db.refresh(collection_run)
        return collection_run

    def get_collection_run(self, run_id: str) -> Optional[CollectionRun]:
        """
        Get a collection run by ID.

        Args:
            run_id: ID of the collection run

        Returns:
            CollectionRun instance if found, None otherwise
        """
        return self.db.query(CollectionRun).filter(CollectionRun.id == run_id).first()

    def get_collections_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Collection]:
        """
        Get all collections for a project.

        Args:
            project_id: ID of the project
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Collection instances
        """
        return (
            self.db.query(Collection)
            .filter(Collection.project_id == project_id)
            .order_by(Collection.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_collection_runs_by_collection(
        self, collection_id: str, skip: int = 0, limit: int = 100
    ) -> List[CollectionRun]:
        """
        Get all collection runs for a collection.

        Args:
            collection_id: ID of the collection
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of CollectionRun instances
        """
        return (
            self.db.query(CollectionRun)
            .filter(CollectionRun.collection_id == collection_id)
            .order_by(CollectionRun.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_collection_runs(self, skip: int = 0, limit: int = 100) -> List[CollectionRun]:
        """
        Get all collection runs across all collections.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of CollectionRun instances
        """
        return self.db.query(CollectionRun).order_by(CollectionRun.created_at.desc()).offset(skip).limit(limit).all()

    def delete_collection_run(self, run_id: str) -> bool:
        """
        Delete a collection run and its reports/results.

        Args:
            run_id: ID of the collection run

        Returns:
            True if deleted, False if not found
        """
        collection_run = self.get_collection_run(run_id)
        if not collection_run:
            return False

        self.db.delete(collection_run)
        self.db.commit()
        return True

    def create_collection_report(
        self,
        run_id: str,
        name: Optional[str] = None,
        total_requests: int = 0,
        successful_requests: int = 0,
        failed_requests: int = 0,
        avg_response_time_ms: Optional[int] = None,
        min_response_time_ms: Optional[int] = None,
        max_response_time_ms: Optional[int] = None,
        p95_response_time_ms: Optional[int] = None,
        p99_response_time_ms: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> CollectionReport:
        """
        Create a new collection report.

        Args:
            run_id: ID of the collection run
            name: Optional report name
            total_requests: Total number of requests
            successful_requests: Number of successful requests
            failed_requests: Number of failed requests
            avg_response_time_ms: Average response time
            min_response_time_ms: Minimum response time
            max_response_time_ms: Maximum response time
            p95_response_time_ms: 95th percentile response time
            p99_response_time_ms: 99th percentile response time
            notes: Optional notes

        Returns:
            Created CollectionReport instance
        """
        report = CollectionReport(
            id=str(uuid.uuid4()),
            collection_run_id=run_id,
            name=name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time_ms,
            min_response_time_ms=min_response_time_ms,
            max_response_time_ms=max_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            p99_response_time_ms=p99_response_time_ms,
            notes=notes,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_collection_reports_by_run(self, run_id: str, skip: int = 0, limit: int = 100) -> List[CollectionReport]:
        """
        Get all reports for a collection run.

        Args:
            run_id: ID of the collection run
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of CollectionReport instances
        """
        return (
            self.db.query(CollectionReport)
            .filter(CollectionReport.collection_run_id == run_id)
            .order_by(CollectionReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_collection_results(
        self, report_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> List[CollectionResult]:
        """
        Get collection results for a report.

        Args:
            report_id: ID of the collection report
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of CollectionResult instances
        """
        query = self.db.query(CollectionResult).filter(CollectionResult.collection_report_id == report_id)
        query = query.order_by(CollectionResult.created_at.desc())
        if limit is not None:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)
        return query.all()

    async def execute_single_request(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, Any]] = None,
        body: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single HTTP request and return timing/metrics.

        Args:
            url: Full URL to request
            method: HTTP method
            headers: Request headers
            body: Request body

        Returns:
            Dictionary with response details and timing
        """
        start_time = time.time()
        result = {
            "url": url,
            "method": method,
            "response_status": None,
            "response_headers": None,
            "response_body": None,
            "error_message": None,
            "is_success": False,
            "response_time_ms": 0,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                request_kwargs = {"headers": headers or {}}
                if body:
                    try:
                        request_kwargs["json"] = json.loads(body)
                    except (json.JSONDecodeError, TypeError):
                        request_kwargs["content"] = body

                response = await client.request(method, url, **request_kwargs)
                end_time = time.time()

                result["response_status"] = response.status_code
                result["response_headers"] = dict(response.headers)
                try:
                    result["response_body"] = response.text[:10000]  # Limit response body size
                except Exception:
                    result["response_body"] = None
                result["is_success"] = 200 <= response.status_code < 400
                result["response_time_ms"] = int((end_time - start_time) * 1000)
        except Exception as e:
            end_time = time.time()
            result["error_message"] = str(e)[:1000]  # Limit error message size
            result["is_success"] = False
            result["response_time_ms"] = int((end_time - start_time) * 1000)

        return result

    async def run_collection(self, run_id: str) -> CollectionRun:
        """
        Execute a collection run and create a report.

        Args:
            run_id: ID of the collection run

        Returns:
            Updated CollectionRun instance
        """
        collection_run = self.get_collection_run(run_id)
        if not collection_run:
            raise ValueError(f"Collection run {run_id} not found")

        # Get collection
        collection = self.db.query(Collection).filter(Collection.id == collection_run.collection_id).first()
        if not collection:
            raise ValueError(f"Collection not found for run {run_id}")

        # Update status to running
        collection_run.status = "running"
        collection_run.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Get all webhooks for this collection (ordered by execution order)
            webhook_service = get_webhook_service(self.db)
            webhooks = webhook_service.get_webhooks_by_collection(str(collection.id))

            if not webhooks:
                raise ValueError(f"No webhooks found for collection {collection.id}")

            # Build endpoints from all webhooks
            endpoints_to_test = []
            for webhook in webhooks:
                # Build full URL with query params if present
                full_url = webhook.url
                if webhook.query_params:
                    from urllib.parse import urlencode

                    query_string = urlencode(webhook.query_params)
                    separator = "&" if "?" in full_url else "?"
                    full_url = f"{full_url}{separator}{query_string}"

                endpoints_to_test.append(
                    {
                        "url": full_url,
                        "method": webhook.method,
                        "headers": webhook.headers,
                        "body": webhook.body_template,
                    }
                )

            # Create a temporary report first (will be updated with metrics)
            report = CollectionReport(
                id=str(uuid.uuid4()),
                collection_run_id=run_id,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
            )
            self.db.add(report)
            self.db.flush()  # Flush to get the report ID

            # Execute collection (results will reference the report)
            results = await self._execute_collection(
                endpoints_to_test,
                collection_run.concurrent_users,
                collection_run.duration_seconds,
                collection_run.requests_per_second,
                report.id,
            )

            # Calculate statistics
            response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
            successful_results = [r for r in results if r.is_success]

            # Update report with metrics
            if response_times:
                report.total_requests = len(results)
                report.successful_requests = len(successful_results)
                report.failed_requests = len(results) - len(successful_results)
                report.avg_response_time_ms = int(statistics.mean(response_times))
                report.min_response_time_ms = min(response_times)
                report.max_response_time_ms = max(response_times)
                if len(response_times) >= 20:
                    sorted_times = sorted(response_times)
                    p95_index = int(len(sorted_times) * 0.95)
                    p99_index = int(len(sorted_times) * 0.99)
                    report.p95_response_time_ms = sorted_times[p95_index]
                    report.p99_response_time_ms = sorted_times[p99_index]

            collection_run.status = "completed"
            collection_run.completed_at = datetime.utcnow()
        except Exception:
            collection_run.status = "failed"
            collection_run.completed_at = datetime.utcnow()
            # Error is logged by the Celery task handler

        self.db.commit()
        self.db.refresh(collection_run)
        return collection_run

    async def _execute_collection(
        self,
        endpoints: List[Dict[str, Any]],
        concurrent_users: int,
        duration_seconds: int,
        requests_per_second: Optional[int],
        report_id: str,
    ) -> List[CollectionResult]:
        """
        Execute the actual collection.

        Args:
            endpoints: List of endpoint configurations
            concurrent_users: Number of concurrent users
            duration_seconds: Duration in seconds
            requests_per_second: Optional rate limit
            report_id: Collection report ID

        Returns:
            List of CollectionResult instances
        """
        results: List[CollectionResult] = []
        end_time = time.time() + duration_seconds
        request_count = 0

        async def worker():
            """Worker coroutine that makes requests"""
            nonlocal request_count
            while time.time() < end_time:
                # Execute all endpoints sequentially in order (one iteration)
                for endpoint in endpoints:
                    request_count += 1

                    # Execute request
                    result_data = await self.execute_single_request(
                        endpoint["url"],
                        endpoint["method"],
                        endpoint.get("headers"),
                        endpoint.get("body"),
                    )

                    # Create result record
                    result = CollectionResult(
                        id=str(uuid.uuid4()),
                        collection_report_id=report_id,
                        endpoint_path=endpoint["url"],
                        method=endpoint["method"],
                        request_headers=endpoint.get("headers"),
                        request_body=endpoint.get("body"),
                        response_status=result_data["response_status"],
                        response_headers=result_data["response_headers"],
                        response_body=result_data["response_body"],
                        response_time_ms=result_data["response_time_ms"],
                        error_message=result_data["error_message"],
                        is_success=1 if result_data["is_success"] else 0,
                    )
                    results.append(result)
                    self.db.add(result)

                # Rate limiting (applied per iteration, not per request)
                if requests_per_second:
                    await asyncio.sleep(1.0 / requests_per_second)

        # Start workers
        workers = [worker() for _ in range(concurrent_users)]
        await asyncio.gather(*workers)

        # Commit all results
        self.db.commit()
        return results


def get_collection_service(db: Session) -> "CollectionService":
    """
    Factory function to create a CollectionService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        CollectionService instance
    """
    return CollectionService(db)
