import asyncio
import websockets
import json
import torch
import logging
from transformers import AutoTokenizer, AutoModel
import soundfile as sf
import io
import numpy as np
from typing import Dict, List, Optional
import base64
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VibeVoiceWebSocketServer:
    def __init__(self, model_path: str = "microsoft/VibeVoice-1.5B"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
    async def initialize_model(self):
        """Load the VibeVoice model asynchronously"""
        logger.info("Loading VibeVoice model...")
        
        # Load in a separate thread to avoid blocking
        def load_model():
            tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            model = AutoModel.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            model.eval()
            return tokenizer, model
        
        self.tokenizer, self.model = await asyncio.get_event_loop().run_in_executor(
            None, load_model
        )
        logger.info(f"Model loaded successfully on {self.device}")
    
    async def generate_streaming_audio(self, text: str, speaker_names: List[str], 
                                     websocket: websockets.WebSocketServerProtocol,
                                     session_id: str):
        """Generate and stream audio in real-time chunks"""
        try:
            # Split text into words for ultra-low latency
            words = text.split()
            chunk_size = 5  # Very small chunks for minimal latency
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                text_chunk = " ".join(chunk_words)
                
                # Add punctuation for better synthesis
                if i + chunk_size >= len(words):
                    text_chunk += "."
                
                start_time = time.time()
                
                # Generate audio for this chunk
                audio_bytes = await self._generate_audio_chunk(
                    text_chunk, speaker_names[0] if speaker_names else "Alice"
                )
                
                generation_time = (time.time() - start_time) * 1000  # ms
                
                if audio_bytes:
                    # Encode audio as base64 for JSON transmission
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    response = {
                        "type": "audio_chunk",
                        "data": audio_base64,
                        "chunk_index": i // chunk_size,
                        "text_chunk": text_chunk,
                        "generation_time_ms": round(generation_time, 2),
                        "session_id": session_id
                    }
                    
                    await websocket.send(json.dumps(response))
                    
                    # Very small delay to prevent overwhelming
                    await asyncio.sleep(0.05)
            
            # Send completion signal
            completion = {
                "type": "generation_complete",
                "session_id": session_id,
                "total_chunks": (len(words) + chunk_size - 1) // chunk_size
            }
            await websocket.send(json.dumps(completion))
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            error_response = {
                "type": "error",
                "message": str(e),
                "session_id": session_id
            }
            await websocket.send(json.dumps(error_response))
    
    async def _generate_audio_chunk(self, text: str, speaker_name: str) -> bytes:
        """Generate audio for a single text chunk"""
        try:
            # Format text for VibeVoice
            formatted_text = f"{speaker_name}: {text}"
            
            # Tokenize
            inputs = self.tokenizer(formatted_text, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate audio
            with torch.no_grad():
                # Run inference in executor to avoid blocking event loop
                audio_output = await asyncio.get_event_loop().run_in_executor(
                    None, self._sync_generate, inputs
                )
            
            # Convert to bytes
            return self._audio_to_bytes(audio_output)
            
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return b""
    
    def _sync_generate(self, inputs):
        """Synchronous generation wrapper"""
        # Note: Adapt this based on actual VibeVoice inference API
        # Check demo/inference_from_file.py for exact usage
        return self.model.generate(**inputs, max_length=512, do_sample=True)
    
    def _audio_to_bytes(self, audio_tensor, sample_rate: int = 24000) -> bytes:
        """Convert audio tensor to WAV bytes"""
        if torch.is_tensor(audio_tensor):
            audio_np = audio_tensor.cpu().numpy().squeeze()
        else:
            audio_np = np.array(audio_tensor).squeeze()
        
        if audio_np.dtype != np.float32:
            audio_np = audio_np.astype(np.float32)
        
        # Normalize audio
        if np.max(np.abs(audio_np)) > 0:
            audio_np = audio_np / np.max(np.abs(audio_np))
        
        buffer = io.BytesIO()
        sf.write(buffer, audio_np, sample_rate, format='WAV')
        return buffer.getvalue()
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle individual client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        session_id = f"session_{int(time.time())}"
        
        logger.info(f"Client connected: {client_id}")
        self.active_connections[client_id] = websocket
        
        # Send welcome message
        welcome = {
            "type": "connection_established",
            "session_id": session_id,
            "server_info": {
                "model": "microsoft/VibeVoice-1.5B",
                "device": str(self.device),
                "sample_rate": 24000
            }
        }
        await websocket.send(json.dumps(welcome))
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data, websocket, session_id)
                except json.JSONDecodeError as e:
                    error = {
                        "type": "error",
                        "message": f"Invalid JSON: {str(e)}",
                        "session_id": session_id
                    }
                    await websocket.send(json.dumps(error))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
    
    async def _handle_message(self, data: dict, websocket: websockets.WebSocketServerProtocol, 
                            session_id: str):
        """Handle incoming messages from clients"""
        message_type = data.get("type")
        
        if message_type == "generate_speech":
            text = data.get("text", "").strip()
            speaker_names = data.get("speaker_names", ["Alice"])
            
            if not text:
                error = {
                    "type": "error",
                    "message": "Text cannot be empty",
                    "session_id": session_id
                }
                await websocket.send(json.dumps(error))
                return
            
            if len(text) > 10000:
                error = {
                    "type": "error", 
                    "message": "Text too long (max 10000 characters)",
                    "session_id": session_id
                }
                await websocket.send(json.dumps(error))
                return
            
            # Start streaming generation
            await self.generate_streaming_audio(text, speaker_names, websocket, session_id)
        
        elif message_type == "ping":
            pong = {
                "type": "pong",
                "timestamp": data.get("timestamp"),
                "session_id": session_id
            }
            await websocket.send(json.dumps(pong))
        
        else:
            error = {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "session_id": session_id
            }
            await websocket.send(json.dumps(error))

async def main():
    """Main server function"""
    server = VibeVoiceWebSocketServer()
    
    # Initialize model
    await server.initialize_model()
    
    # Start WebSocket server
    logger.info("Starting WebSocket server on ws://localhost:8765")
    async with websockets.serve(
        server.handle_client, 
        "localhost", 
        8765,
        ping_interval=20,
        ping_timeout=10
    ):
        logger.info("VibeVoice WebSocket TTS server is running...")
        logger.info("Connect to: ws://localhost:8765")
        logger.info("Message format: {\"type\": \"generate_speech\", \"text\": \"Hello world\", \"speaker_names\": [\"Alice\"]}")
        
        # Keep server running
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
