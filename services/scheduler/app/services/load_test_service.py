"""
Load test service for executing load/stress tests on API endpoints.
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

from app.models.collections import Collection
from app.models.load_test_reports import LoadTestReport
from app.models.load_test_results import LoadTestResult
from app.models.load_test_runs import LoadTestRun
from app.services.webhook_service import get_webhook_service


class LoadTestService:
    """Service class for load testing operations"""

    def __init__(self, db: Session):
        """
        Initialize the load test service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_load_test_run(
        self,
        collection_id: str,
        concurrent_users: int = 10,
        duration_seconds: int = 60,
        requests_per_second: Optional[int] = None,
    ) -> LoadTestRun:
        """
        Create a new load test run from a collection.

        Args:
            collection_id: ID of the webhook collection
            concurrent_users: Number of concurrent users
            duration_seconds: Duration in seconds
            requests_per_second: Optional rate limit

        Returns:
            Created LoadTestRun instance
        """
        load_test_run = LoadTestRun(
            id=str(uuid.uuid4()),
            collection_id=collection_id,
            status="pending",
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            requests_per_second=requests_per_second,
        )
        self.db.add(load_test_run)
        self.db.commit()
        self.db.refresh(load_test_run)
        return load_test_run

    def get_load_test_run(self, run_id: str) -> Optional[LoadTestRun]:
        """
        Get a load test run by ID.

        Args:
            run_id: ID of the load test run

        Returns:
            LoadTestRun instance if found, None otherwise
        """
        return self.db.query(LoadTestRun).filter(LoadTestRun.id == run_id).first()

    def get_load_test_runs_by_collection(
        self, collection_id: str, skip: int = 0, limit: int = 100
    ) -> List[LoadTestRun]:
        """
        Get all load test runs for a collection.

        Args:
            collection_id: ID of the collection
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of LoadTestRun instances
        """
        return (
            self.db.query(LoadTestRun)
            .filter(LoadTestRun.collection_id == collection_id)
            .order_by(LoadTestRun.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_load_test_runs(self, skip: int = 0, limit: int = 100) -> List[LoadTestRun]:
        """
        Get all load test runs across all collections.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of LoadTestRun instances
        """
        return self.db.query(LoadTestRun).order_by(LoadTestRun.created_at.desc()).offset(skip).limit(limit).all()

    def delete_load_test_run(self, run_id: str) -> bool:
        """
        Delete a load test run and its reports/results.

        Args:
            run_id: ID of the load test run

        Returns:
            True if deleted, False if not found
        """
        load_test_run = self.get_load_test_run(run_id)
        if not load_test_run:
            return False

        self.db.delete(load_test_run)
        self.db.commit()
        return True

    def create_load_test_report(
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
    ) -> LoadTestReport:
        """
        Create a new load test report.

        Args:
            run_id: ID of the load test run
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
            Created LoadTestReport instance
        """
        report = LoadTestReport(
            id=str(uuid.uuid4()),
            load_test_run_id=run_id,
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

    def get_load_test_reports_by_run(self, run_id: str, skip: int = 0, limit: int = 100) -> List[LoadTestReport]:
        """
        Get all reports for a load test run.

        Args:
            run_id: ID of the load test run
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of LoadTestReport instances
        """
        return (
            self.db.query(LoadTestReport)
            .filter(LoadTestReport.load_test_run_id == run_id)
            .order_by(LoadTestReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_load_test_results(
        self, report_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> List[LoadTestResult]:
        """
        Get load test results for a report.

        Args:
            report_id: ID of the load test report
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of LoadTestResult instances
        """
        query = self.db.query(LoadTestResult).filter(LoadTestResult.load_test_report_id == report_id)
        query = query.order_by(LoadTestResult.created_at.desc())
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

    async def run_load_test(self, run_id: str) -> LoadTestRun:
        """
        Execute a load test run and create a report.

        Args:
            run_id: ID of the load test run

        Returns:
            Updated LoadTestRun instance
        """
        load_test_run = self.get_load_test_run(run_id)
        if not load_test_run:
            raise ValueError(f"Load test run {run_id} not found")

        # Get collection
        collection = self.db.query(Collection).filter(Collection.id == load_test_run.collection_id).first()
        if not collection:
            raise ValueError(f"Collection not found for run {run_id}")

        # Update status to running
        load_test_run.status = "running"
        load_test_run.started_at = datetime.utcnow()
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
                        "order": webhook.order or 0,
                    }
                )

            # Sort by order to ensure sequential execution
            endpoints_to_test.sort(key=lambda x: x.get("order", 0))

            # Create a temporary report first (will be updated with metrics)
            report = LoadTestReport(
                id=str(uuid.uuid4()),
                load_test_run_id=run_id,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
            )
            self.db.add(report)
            self.db.flush()  # Flush to get the report ID

            # Execute load test (results will reference the report)
            results = await self._execute_load_test(
                endpoints_to_test,
                load_test_run.concurrent_users,
                load_test_run.duration_seconds,
                load_test_run.requests_per_second,
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

            load_test_run.status = "completed"
            load_test_run.completed_at = datetime.utcnow()
        except Exception:
            load_test_run.status = "failed"
            load_test_run.completed_at = datetime.utcnow()
            # Error is logged by the Celery task handler

        self.db.commit()
        self.db.refresh(load_test_run)
        return load_test_run

    async def _execute_load_test(
        self,
        endpoints: List[Dict[str, Any]],
        concurrent_users: int,
        duration_seconds: int,
        requests_per_second: Optional[int],
        report_id: str,
    ) -> List[LoadTestResult]:
        """
        Execute the actual load test.

        Args:
            endpoints: List of endpoint configurations
            concurrent_users: Number of concurrent users
            duration_seconds: Duration in seconds
            requests_per_second: Optional rate limit
            report_id: Load test report ID

        Returns:
            List of LoadTestResult instances
        """
        results: List[LoadTestResult] = []
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
                    result = LoadTestResult(
                        id=str(uuid.uuid4()),
                        load_test_report_id=report_id,
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


def get_load_test_service(db: Session) -> "LoadTestService":
    """
    Factory function to create a LoadTestService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        LoadTestService instance
    """
    return LoadTestService(db)
