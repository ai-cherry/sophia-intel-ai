#!/usr/bin/env python3
"""
WebRTC Voice System Integration Test
Tests the complete voice pipeline with isolation to prevent cross-talk
"""

import asyncio
import json
import os
import sys
import time
from typing import Optional
import aiohttp
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_TIMEOUT = 30  # seconds


class VoiceSystemTest:
    """Test harness for WebRTC voice system"""
    
    def __init__(self, test_id: str = "test"):
        self.test_id = test_id
        self.api_url = API_URL
        self.session_id = None
        self.results = {
            "health_check": False,
            "webrtc_offer": False,
            "control_ws": False,
            "audio_ws": False,
            "session_isolation": False,
            "barge_in": False,
            "errors": []
        }
        
    async def test_health_check(self):
        """Test voice system health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/voice/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"✅ Health check passed: {data}")
                        self.results["health_check"] = True
                        return True
                    else:
                        error = f"Health check failed: {resp.status}"
                        logger.error(f"❌ {error}")
                        self.results["errors"].append(error)
                        return False
        except Exception as e:
            error = f"Health check error: {e}"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
            
    async def test_webrtc_offer(self):
        """Test WebRTC offer/answer exchange"""
        try:
            # Create mock SDP offer
            mock_offer = {
                "sdp": "v=0\\r\\no=- 123456 2 IN IP4 127.0.0.1\\r\\n" +
                       "s=-\\r\\nt=0 0\\r\\na=group:BUNDLE 0\\r\\n" +
                       "m=audio 9 UDP/TLS/RTP/SAVPF 111\\r\\n" +
                       "c=IN IP4 0.0.0.0\\r\\na=rtcp:9 IN IP4 0.0.0.0\\r\\n",
                "session_id": f"{self.test_id}_{time.time()}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/voice/webrtc/offer",
                    json=mock_offer
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.session_id = data.get("session_id")
                        logger.info(f"✅ WebRTC offer accepted, session: {self.session_id}")
                        self.results["webrtc_offer"] = True
                        return True
                    else:
                        error = f"WebRTC offer failed: {resp.status}"
                        logger.error(f"❌ {error}")
                        self.results["errors"].append(error)
                        return False
        except Exception as e:
            error = f"WebRTC offer error: {e}"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
            
    async def test_control_websocket(self):
        """Test control WebSocket connection"""
        try:
            ws_url = self.api_url.replace("http", "ws") + "/api/voice/control"
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url) as ws:
                    # Send session ID
                    await ws.send_json({"session_id": self.session_id})
                    
                    # Test barge-in command
                    await ws.send_json({"type": "bargeIn"})
                    
                    # Wait for response
                    msg = await asyncio.wait_for(ws.receive(), timeout=5)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "bargeIn_response":
                            logger.info(f"✅ Control WebSocket working, barge-in: {data.get('success')}")
                            self.results["control_ws"] = True
                            self.results["barge_in"] = data.get("success", False)
                            
                    # Test metrics
                    await ws.send_json({"type": "getMetrics"})
                    msg = await asyncio.wait_for(ws.receive(), timeout=5)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        logger.info(f"📊 Session metrics: {data.get('data')}")
                        
                    await ws.close()
                    return True
                    
        except asyncio.TimeoutError:
            error = "Control WebSocket timeout"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
        except Exception as e:
            error = f"Control WebSocket error: {e}"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
            
    async def test_audio_websocket(self):
        """Test audio WebSocket fallback"""
        try:
            ws_url = self.api_url.replace("http", "ws") + "/api/voice/ws"
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url) as ws:
                    # Send test audio (silent PCM)
                    test_audio = bytes(320)  # 10ms of silence at 16kHz
                    await ws.send_bytes(test_audio)
                    
                    # Send synthesize command
                    await ws.send_json({
                        "type": "synthesize",
                        "data": {"text": "Test audio response"}
                    })
                    
                    # Wait for audio response
                    msg = await asyncio.wait_for(ws.receive(), timeout=5)
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        logger.info(f"✅ Audio WebSocket working, received {len(msg.data)} bytes")
                        self.results["audio_ws"] = True
                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        logger.info(f"📝 Received transcript: {data}")
                        
                    await ws.close()
                    return True
                    
        except asyncio.TimeoutError:
            error = "Audio WebSocket timeout"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
        except Exception as e:
            error = f"Audio WebSocket error: {e}"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
            
    async def test_session_isolation(self):
        """Test that sessions are properly isolated"""
        try:
            # Create two different sessions
            sessions = []
            
            for i in range(2):
                mock_offer = {
                    "sdp": "v=0\\r\\no=- 123456 2 IN IP4 127.0.0.1\\r\\n",
                    "session_id": f"isolation_test_{i}_{time.time()}"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/api/voice/webrtc/offer",
                        json=mock_offer
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            sessions.append(data.get("session_id"))
                            
            # Check active sessions
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/voice/sessions") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        active_sessions = [s["id"] for s in data.get("sessions", [])]
                        
                        # Verify both sessions exist and are different
                        if len(set(sessions)) == 2:
                            logger.info(f"✅ Session isolation verified: {len(sessions)} unique sessions")
                            self.results["session_isolation"] = True
                            
                            # Cleanup sessions
                            for sid in sessions:
                                await session.delete(f"{self.api_url}/api/voice/sessions/{sid}")
                            return True
                        else:
                            error = "Session isolation failed - sessions not unique"
                            logger.error(f"❌ {error}")
                            self.results["errors"].append(error)
                            return False
                            
        except Exception as e:
            error = f"Session isolation test error: {e}"
            logger.error(f"❌ {error}")
            self.results["errors"].append(error)
            return False
            
    async def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("=" * 60)
        logger.info("🎤 WebRTC Voice System Integration Test")
        logger.info("=" * 60)
        
        # Run tests
        await self.test_health_check()
        
        if self.results["health_check"]:
            await self.test_webrtc_offer()
            
            if self.results["webrtc_offer"]:
                # Run control and audio tests in parallel
                await asyncio.gather(
                    self.test_control_websocket(),
                    self.test_audio_websocket(),
                    return_exceptions=True
                )
                
            await self.test_session_isolation()
            
        # Print results
        logger.info("\n" + "=" * 60)
        logger.info("📊 Test Results Summary")
        logger.info("=" * 60)
        
        passed = sum(1 for v in self.results.values() if v is True)
        total = len([k for k in self.results.keys() if k != "errors"])
        
        for test, result in self.results.items():
            if test != "errors":
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"{test:20s}: {status}")
                
        logger.info("-" * 60)
        logger.info(f"Total: {passed}/{total} tests passed")
        
        if self.results["errors"]:
            logger.info("\n❌ Errors:")
            for error in self.results["errors"]:
                logger.error(f"  - {error}")
                
        return passed == total


async def main():
    """Main test runner"""
    # Check environment
    logger.info(f"Testing against: {API_URL}")
    
    # Check required environment variables
    missing = []
    if not os.getenv("DEEPGRAM_API_KEY"):
        missing.append("DEEPGRAM_API_KEY")
    if not os.getenv("ELEVENLABS_API_KEY"):
        missing.append("ELEVENLABS_API_KEY")
    if not os.getenv("ELEVENLABS_VOICE_ID"):
        missing.append("ELEVENLABS_VOICE_ID")
        
    if missing:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing)}")
        logger.warning("Some tests may fail without proper API keys")
        
    # Run tests
    tester = VoiceSystemTest()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())