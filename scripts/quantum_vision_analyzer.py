"""
Quantum Vision Analyzer for BrainOS.
Provides advanced image analysis with quantum computing techniques.
"""

import os
import cv2
import numpy as np
import base64
import logging
from typing import Dict, Any, Optional, List, Tuple
import matplotlib.pyplot as plt
from PIL import Image
import io

# Import qiskit if available
try:
    from qiskit import QuantumCircuit, execute, Aer
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quantum_vision")

class QuantumVisionAnalyzer:
    """Advanced image analyzer that uses quantum computing techniques when available."""
    
    def __init__(self):
        """Initialize the quantum vision analyzer."""
        self.simulator = None
        if QISKIT_AVAILABLE:
            try:
                self.simulator = Aer.get_backend('qasm_simulator')
                logger.info("Quantum simulator initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize quantum simulator: {e}")
        else:
            logger.warning("Qiskit not available. Running in classical mode only.")
        
        # Initialize OpenCV-based classical analyzer
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def analyze_image(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze an image using quantum and classical techniques.
        
        Args:
            image_data: Base64 encoded image or path to image file
            
        Returns:
            Dict with analysis results
        """
        try:
            # Convert input to OpenCV image
            if image_data.startswith('data:image'):
                # Handle base64 encoded image
                image_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(image_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            elif os.path.isfile(image_data):
                # Handle image file path
                img = cv2.imread(image_data)
            else:
                raise ValueError("Invalid image data format")
            
            if img is None:
                raise ValueError("Failed to load image")
            
            # Perform classical analysis
            classical_results = self._classical_analyze(img)
            
            # Perform quantum analysis if available
            quantum_results = {}
            if QISKIT_AVAILABLE and self.simulator:
                quantum_results = self._quantum_analyze(img)
            
            # Combine results
            return {
                "classical_analysis": classical_results,
                "quantum_analysis": quantum_results,
                "image_properties": {
                    "width": img.shape[1],
                    "height": img.shape[0],
                    "channels": img.shape[2] if len(img.shape) > 2 else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {"error": str(e)}
    
    def _classical_analyze(self, img: np.ndarray) -> Dict[str, Any]:
        """Perform classical image analysis using OpenCV."""
        results = {}
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 100, 200)
        results["edge_percentage"] = np.count_nonzero(edges) / edges.size
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        results["faces_detected"] = len(faces)
        if len(faces) > 0:
            results["face_locations"] = faces.tolist()
        
        # Color analysis
        if len(img.shape) == 3:  # Color image
            # Calculate average color
            avg_color_per_channel = np.mean(img, axis=(0, 1))
            results["avg_color"] = {
                "blue": float(avg_color_per_channel[0]),
                "green": float(avg_color_per_channel[1]),
                "red": float(avg_color_per_channel[2])
            }
            
            # Calculate color histogram
            color_hist = {}
            for i, color in enumerate(['blue', 'green', 'red']):
                hist = cv2.calcHist([img], [i], None, [8], [0, 256])
                color_hist[color] = hist.flatten().tolist()
            results["color_histogram"] = color_hist
        
        # Image complexity based on entropy
        entropy = self._calculate_entropy(gray)
        results["entropy"] = float(entropy)
        
        return results
    
    def _quantum_analyze(self, img: np.ndarray) -> Dict[str, Any]:
        """Perform quantum-inspired image analysis."""
        if not QISKIT_AVAILABLE or self.simulator is None:
            return {"error": "Quantum analysis not available"}
        
        results = {}
        
        try:
            # Resize and convert to grayscale for quantum processing
            small_img = cv2.resize(img, (16, 16))
            if len(small_img.shape) == 3:
                small_gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
            else:
                small_gray = small_img
            
            # Normalize pixel values
            normalized = small_gray / 255.0
            
            # Create a simple 8-qubit circuit based on image data
            qc = QuantumCircuit(8, 8)
            
            # Use the center 8 pixels to determine qubit states
            center_pixels = normalized[7:9, 7:9].flatten()
            for i, pixel in enumerate(center_pixels[:8]):
                if pixel > 0.5:  # If pixel is bright, apply X gate
                    qc.x(i)
            
            # Apply some quantum operations
            qc.h(range(8))  # Hadamard gate on all qubits
            for i in range(7):
                qc.cx(i, i+1)  # CNOT gates
            
            # Add measurements
            qc.measure(range(8), range(8))
            
            # Execute the circuit
            job = execute(qc, self.simulator, shots=1024)
            result = job.result()
            counts = result.get_counts(qc)
            
            # Process results
            results["quantum_states"] = {
                k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
            }
            
            # Calculate quantum entropy
            q_entropy = 0
            total_shots = sum(counts.values())
            for count in counts.values():
                prob = count / total_shots
                q_entropy -= prob * np.log2(prob) if prob > 0 else 0
            
            results["quantum_entropy"] = float(q_entropy)
            results["interpretation"] = self._interpret_quantum_results(counts)
            
        except Exception as e:
            logger.error(f"Error in quantum analysis: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _calculate_entropy(self, img: np.ndarray) -> float:
        """Calculate the entropy of an image."""
        # Calculate histogram
        hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        hist = hist / hist.sum()
        
        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-7))
        return float(entropy)
    
    def _interpret_quantum_results(self, counts: Dict[str, int]) -> Dict[str, Any]:
        """Interpret quantum circuit results for image analysis."""
        total_shots = sum(counts.values())
        most_common = max(counts.items(), key=lambda x: x[1])
        binary_str = most_common[0]
        
        # Convert binary to int for a simple property estimation
        if binary_str:
            value = int(binary_str, 2) % 100
        else:
            value = 0
            
        # Map this value to an image property
        if value < 20:
            category = "low complexity"
        elif value < 50:
            category = "medium complexity"
        else:
            category = "high complexity"
            
        interpretation = {
            "dominant_pattern": binary_str,
            "pattern_frequency": most_common[1] / total_shots,
            "estimated_complexity": value,
            "complexity_category": category
        }
        
        return interpretation
    
    def visualize_analysis(self, image_data: str, results: Dict[str, Any]) -> bytes:
        """
        Create a visualization of the analysis results.
        
        Args:
            image_data: Original image data
            results: Analysis results
            
        Returns:
            Bytes of the visualization image
        """
        try:
            # Load the image
            if image_data.startswith('data:image'):
                # Handle base64 encoded image
                image_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(image_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            elif os.path.isfile(image_data):
                # Handle image file path
                img = cv2.imread(image_data)
            else:
                raise ValueError("Invalid image data format")
            
            # Convert BGR to RGB for matplotlib
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Create a figure with subplots
            fig, axs = plt.subplots(2, 2, figsize=(12, 10))
            
            # Original image
            axs[0, 0].imshow(img_rgb)
            axs[0, 0].set_title('Original Image')
            axs[0, 0].axis('off')
            
            # Edge detection visualization
            if 'classical_analysis' in results:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                axs[0, 1].imshow(edges, cmap='gray')
                axs[0, 1].set_title(f'Edge Detection ({results["classical_analysis"]["edge_percentage"]:.2%})')
                axs[0, 1].axis('off')
                
                # Face detection visualization
                img_with_faces = img_rgb.copy()
                if results['classical_analysis'].get('faces_detected', 0) > 0:
                    for (x, y, w, h) in results['classical_analysis'].get('face_locations', []):
                        cv2.rectangle(img_with_faces, (x, y), (x+w, y+h), (0, 255, 0), 2)
                axs[1, 0].imshow(img_with_faces)
                axs[1, 0].set_title(f'Face Detection ({results["classical_analysis"]["faces_detected"]} faces)')
                axs[1, 0].axis('off')
            
            # Quantum analysis visualization
            if 'quantum_analysis' in results and 'quantum_states' in results['quantum_analysis']:
                # Plot top quantum states
                states = results['quantum_analysis']['quantum_states']
                labels = list(states.keys())
                sizes = list(states.values())
                axs[1, 1].pie(sizes, labels=labels, autopct='%1.1f%%')
                axs[1, 1].set_title('Quantum State Distribution')
            
            # Add overall caption with analysis summary
            complexity = "Unknown"
            if 'quantum_analysis' in results and 'interpretation' in results['quantum_analysis']:
                complexity = results['quantum_analysis']['interpretation'].get('complexity_category', 'Unknown')
            
            fig.suptitle(f'Image Analysis Summary\nComplexity: {complexity}', fontsize=16)
            plt.tight_layout()
            
            # Convert plot to image
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            # Close the plot to free memory
            plt.close(fig)
            
            return buf.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            # Return a simple error image
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f"Visualization Error: {str(e)}", 
                    ha='center', va='center', fontsize=12)
            ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            return buf.getvalue()


# Test function
def test_analyzer():
    """Test the quantum vision analyzer with a sample image."""
    analyzer = QuantumVisionAnalyzer()
    
    # Find a test image
    test_image_path = None
    potential_paths = [
        "test_image.jpg",
        "tests/test_image.jpg",
        "../tests/test_image.jpg",
        "sample_image.jpg",
        "../sample_image.jpg"
    ]
    
    for path in potential_paths:
        if os.path.isfile(path):
            test_image_path = path
            break
    
    if not test_image_path:
        print("No test image found. Please provide an image path.")
        return
    
    print(f"Analyzing image: {test_image_path}")
    results = analyzer.analyze_image(test_image_path)
    
    # Print results
    print("Analysis results:")
    print(json.dumps(results, indent=2))
    
    # Generate and save visualization
    viz_data = analyzer.visualize_analysis(test_image_path, results)
    with open("quantum_analysis.png", "wb") as f:
        f.write(viz_data)
    print("Visualization saved to quantum_analysis.png")


if __name__ == "__main__":
    import json
    test_analyzer()