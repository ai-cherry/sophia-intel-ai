"""
Tests for SOPHIALambdaMaster
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from sophia.core.lambda_master import SOPHIALambdaMaster, LambdaInstance, LambdaJob, LambdaInstanceType


@pytest.fixture
def lambda_master():
    """Create Lambda master instance for testing."""
    with patch.dict('os.environ', {'LAMBDA_API_KEY': 'test-key'}):
        return SOPHIALambdaMaster()


@pytest.fixture
def mock_instance():
    """Mock Lambda instance data."""
    return {
        "id": "test-instance-123",
        "name": "test-instance",
        "instance_type": {"name": "gpu_1x_a100"},
        "region": {"name": "us-west-1"},
        "status": "active",
        "ip": "1.2.3.4",
        "ssh_key_names": [{"name": "test-key"}],
        "file_system_names": []
    }


@pytest.fixture
def mock_instance_type():
    """Mock Lambda instance type data."""
    return {
        "name": "gpu_1x_a100",
        "price_cents_per_hour": 110,
        "description": "1x NVIDIA A100 (40 GB PCIe)",
        "specs": {
            "vcpus": 30,
            "memory_gib": 200,
            "storage_gib": 1400
        }
    }


class TestSOPHIALambdaMaster:
    """Test cases for SOPHIALambdaMaster."""
    
    def test_initialization(self):
        """Test Lambda master initialization."""
        with patch.dict('os.environ', {'LAMBDA_API_KEY': 'test-key'}):
            master = SOPHIALambdaMaster()
            assert master.api_key == 'test-key'
            assert master.base_url == "https://cloud.lambdalabs.com/api/v1"
            assert master.active_instances == {}
            assert master.total_cost_cents == 0
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            master = SOPHIALambdaMaster()
            assert master.api_key is None
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, lambda_master):
        """Test successful API request."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response
            
            result = await lambda_master._make_request("GET", "/test")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_make_request_error(self, lambda_master):
        """Test API request error handling."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": {"message": "Bad request"}})
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="Lambda API error: Bad request"):
                await lambda_master._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_no_api_key(self):
        """Test API request without API key."""
        master = SOPHIALambdaMaster()
        master.api_key = None
        
        with pytest.raises(RuntimeError, match="Lambda API key not configured"):
            await master._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_list_instance_types(self, lambda_master, mock_instance_type):
        """Test listing instance types."""
        mock_response = {"data": [mock_instance_type]}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            instance_types = await lambda_master.list_instance_types()
            
            assert len(instance_types) == 1
            assert isinstance(instance_types[0], LambdaInstanceType)
            assert instance_types[0].name == "gpu_1x_a100"
            assert instance_types[0].price_cents_per_hour == 110
    
    @pytest.mark.asyncio
    async def test_list_regions(self, lambda_master):
        """Test listing regions."""
        mock_response = {"data": [{"name": "us-west-1"}, {"name": "us-east-1"}]}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            regions = await lambda_master.list_regions()
            
            assert regions == ["us-west-1", "us-east-1"]
    
    @pytest.mark.asyncio
    async def test_list_ssh_keys(self, lambda_master):
        """Test listing SSH keys."""
        mock_response = {"data": [{"name": "test-key", "public_key": "ssh-rsa ..."}]}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            ssh_keys = await lambda_master.list_ssh_keys()
            
            assert len(ssh_keys) == 1
            assert ssh_keys[0]["name"] == "test-key"
    
    @pytest.mark.asyncio
    async def test_spin_up_gpu_success(self, lambda_master):
        """Test successful GPU instance launch."""
        mock_response = {"data": {"instance_ids": ["instance-123"]}}
        mock_instance_types = [LambdaInstanceType("gpu_1x_a100", 110, "Test GPU", {})]
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response), \
             patch.object(lambda_master, 'list_instance_types', return_value=mock_instance_types), \
             patch.object(lambda_master, 'list_ssh_keys', return_value=[{"name": "test-key"}]):
            
            instances = await lambda_master.spin_up_gpu(
                instance_type="gpu_1x_a100",
                region="us-west-1",
                name="test-instance"
            )
            
            assert len(instances) == 1
            assert instances[0].id == "instance-123"
            assert instances[0].instance_type == "gpu_1x_a100"
            assert instances[0].region == "us-west-1"
            assert instances[0].status == "booting"
            assert "instance-123" in lambda_master.active_instances
    
    @pytest.mark.asyncio
    async def test_list_instances(self, lambda_master, mock_instance):
        """Test listing instances."""
        mock_response = {"data": [mock_instance]}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            instances = await lambda_master.list_instances()
            
            assert len(instances) == 1
            assert isinstance(instances[0], LambdaInstance)
            assert instances[0].id == "test-instance-123"
            assert instances[0].status == "active"
            assert "test-instance-123" in lambda_master.active_instances
    
    @pytest.mark.asyncio
    async def test_get_instance(self, lambda_master, mock_instance):
        """Test getting specific instance."""
        mock_response = {"data": mock_instance}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            instance = await lambda_master.get_instance("test-instance-123")
            
            assert instance is not None
            assert instance.id == "test-instance-123"
            assert instance.status == "active"
    
    @pytest.mark.asyncio
    async def test_get_instance_not_found(self, lambda_master):
        """Test getting non-existent instance."""
        mock_response = {"data": {}}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            instance = await lambda_master.get_instance("nonexistent")
            
            assert instance is None
    
    @pytest.mark.asyncio
    async def test_run_job(self, lambda_master):
        """Test running a job."""
        job_spec = LambdaJob(
            name="test-job",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            ssh_key_names=["test-key"]
        )
        
        mock_instances = [LambdaInstance(
            id="instance-123",
            name="test-job",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            status="booting"
        )]
        
        with patch.object(lambda_master, 'spin_up_gpu', return_value=mock_instances), \
             patch.object(lambda_master, '_wait_for_instances_active'):
            
            instances = await lambda_master.run_job(job_spec)
            
            assert len(instances) == 1
            assert instances[0].name == "test-job"
    
    @pytest.mark.asyncio
    async def test_tear_down_success(self, lambda_master):
        """Test successful instance termination."""
        # Add instance to active instances
        instance = LambdaInstance(
            id="instance-123",
            name="test",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            status="active"
        )
        lambda_master.active_instances["instance-123"] = instance
        
        mock_response = {"success": True}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            result = await lambda_master.tear_down("instance-123")
            
            assert result is True
            assert "instance-123" not in lambda_master.active_instances
    
    @pytest.mark.asyncio
    async def test_tear_down_all(self, lambda_master):
        """Test terminating all instances."""
        # Add multiple instances
        for i in range(3):
            instance = LambdaInstance(
                id=f"instance-{i}",
                name=f"test-{i}",
                instance_type="gpu_1x_a100",
                region="us-west-1",
                status="active"
            )
            lambda_master.active_instances[f"instance-{i}"] = instance
        
        mock_response = {"success": True}
        
        with patch.object(lambda_master, '_make_request', return_value=mock_response):
            terminated_count = await lambda_master.tear_down_all()
            
            assert terminated_count == 3
            assert len(lambda_master.active_instances) == 0
    
    @pytest.mark.asyncio
    async def test_wait_for_instances_active(self, lambda_master):
        """Test waiting for instances to become active."""
        mock_instance = LambdaInstance(
            id="instance-123",
            name="test",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            status="active"
        )
        
        with patch.object(lambda_master, 'get_instance', return_value=mock_instance):
            # Should complete without raising
            await lambda_master._wait_for_instances_active(["instance-123"], timeout_seconds=1)
    
    @pytest.mark.asyncio
    async def test_wait_for_instances_timeout(self, lambda_master):
        """Test timeout while waiting for instances."""
        mock_instance = LambdaInstance(
            id="instance-123",
            name="test",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            status="booting"  # Never becomes active
        )
        
        with patch.object(lambda_master, 'get_instance', return_value=mock_instance):
            with pytest.raises(RuntimeError, match="Timeout waiting for instances"):
                await lambda_master._wait_for_instances_active(["instance-123"], timeout_seconds=1, poll_interval=0.1)
    
    def test_get_cost_summary(self, lambda_master):
        """Test cost summary generation."""
        # Add some active instances
        instance = LambdaInstance(
            id="instance-123",
            name="test",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        lambda_master.active_instances["instance-123"] = instance
        
        summary = lambda_master.get_cost_summary()
        
        assert summary["active_instances"] == 1
        assert len(summary["instances"]) == 1
        assert summary["instances"][0]["id"] == "instance-123"
    
    @pytest.mark.asyncio
    async def test_get_health_status_healthy(self, lambda_master):
        """Test health status when healthy."""
        with patch.object(lambda_master, 'list_regions', return_value=["us-west-1"]), \
             patch.object(lambda_master, 'list_instances', return_value=[]):
            
            health = await lambda_master.get_health_status()
            
            assert health["status"] == "healthy"
            assert health["api_connected"] is True
            assert "timestamp" in health
    
    @pytest.mark.asyncio
    async def test_get_health_status_unhealthy(self, lambda_master):
        """Test health status when unhealthy."""
        with patch.object(lambda_master, 'list_regions', side_effect=Exception("API error")):
            
            health = await lambda_master.get_health_status()
            
            assert health["status"] == "unhealthy"
            assert health["api_connected"] is False
            assert "error" in health
    
    @pytest.mark.asyncio
    async def test_close(self, lambda_master):
        """Test cleanup on close."""
        # Should complete without error
        await lambda_master.close()


class TestLambdaDataClasses:
    """Test Lambda data classes."""
    
    def test_lambda_instance_creation(self):
        """Test LambdaInstance creation."""
        instance = LambdaInstance(
            id="test-123",
            name="test-instance",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            status="active",
            ip="1.2.3.4"
        )
        
        assert instance.id == "test-123"
        assert instance.name == "test-instance"
        assert instance.instance_type == "gpu_1x_a100"
        assert instance.region == "us-west-1"
        assert instance.status == "active"
        assert instance.ip == "1.2.3.4"
    
    def test_lambda_instance_type_creation(self):
        """Test LambdaInstanceType creation."""
        instance_type = LambdaInstanceType(
            name="gpu_1x_a100",
            price_cents_per_hour=110,
            description="1x NVIDIA A100",
            specs={"vcpus": 30, "memory_gib": 200}
        )
        
        assert instance_type.name == "gpu_1x_a100"
        assert instance_type.price_cents_per_hour == 110
        assert instance_type.description == "1x NVIDIA A100"
        assert instance_type.specs["vcpus"] == 30
    
    def test_lambda_job_creation(self):
        """Test LambdaJob creation."""
        job = LambdaJob(
            name="test-job",
            instance_type="gpu_1x_a100",
            region="us-west-1",
            ssh_key_names=["test-key"],
            quantity=2
        )
        
        assert job.name == "test-job"
        assert job.instance_type == "gpu_1x_a100"
        assert job.region == "us-west-1"
        assert job.ssh_key_names == ["test-key"]
        assert job.quantity == 2


@pytest.mark.asyncio
async def test_example_jobs():
    """Test example job specifications."""
    from sophia.core.lambda_master import EXAMPLE_JOBS
    
    assert "training_job" in EXAMPLE_JOBS
    assert "inference_job" in EXAMPLE_JOBS
    assert "research_job" in EXAMPLE_JOBS
    
    training_job = EXAMPLE_JOBS["training_job"]
    assert training_job.name == "sophia-model-training"
    assert training_job.instance_type == "gpu_1x_a100"
    assert training_job.quantity == 1

