import os
import json
import time
from typing import List, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from PIL import Image, ImageOps, ImageFilter

# --- Core Processing Logic (Must be picklable for Multiprocessing) ---

def apply_pipeline_to_image(img_path: str, pipeline_steps: List[dict], output_dir: str, pipeline_name: str):
    """
    Worker function to process a single (Image, Pipeline) pair.
    """
    try:
        start_time = time.time()
        img_name = os.path.splitext(os.path.basename(img_path))[0]
        ext = os.path.splitext(img_path)[1]
        ops = [step.get("transform") for step in pipeline_steps]
        ops_str = "_".join(ops)
        out_filename = f"{img_name}_{pipeline_name}_{ops_str}{ext}"
        out_path = os.path.join(output_dir, out_filename)

        print("Processing: ", img_path, os.path.basename(img_path))

        # Optimization: Don't re-process if exists (unless forced)
        # if os.path.exists(out_path): return

        with Image.open(img_path) as img:
            processed_img = img
            for step in pipeline_steps:
                op = step.get("transform")
                args = step.get("args", [])
                
                # --- Map Transformations ---
                if op == "grayscale":
                    processed_img = ImageOps.grayscale(processed_img)
                elif op == "flip_horizontally":
                    processed_img = ImageOps.mirror(processed_img)
                elif op == "flip_vertically":
                    processed_img = ImageOps.flip(processed_img)
                elif op == "scale":
                    factor = args[0]
                    # Pillow resize requires integer size
                    new_size = (int(processed_img.width * factor), int(processed_img.height * factor))
                    processed_img = processed_img.resize(new_size)
                elif op == "rotate":
                    processed_img = processed_img.rotate(args[0])
                elif op == "blur":
                    radius = args[0] if args else 2
                    processed_img = processed_img.filter(ImageFilter.BoxBlur(radius))
                else:
                    print(f"Unknown op: {op}")

            processed_img.save(out_path)
            # print(f"Saved {out_path} in {time.time() - start_time:.4f}s")
            return out_path

    except Exception as e:
        return f"Error: {e}"

# --- Orchestrator ---

class ImageProcessor:
    def __init__(self, output_dir: "out"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"Output directory located at: {os.path.abspath(output_dir)}")


    def run_sequential(self, images: List[str], pipelines: dict):
        print("Running Sequential...")
        start = time.time()
        for img_path in images:
            for pipe_name, steps in pipelines.items():
                apply_pipeline_to_image(img_path, steps, self.output_dir, pipe_name)
        print(f"Sequential finished in {time.time() - start:.4f}s")

    def run_parallel(self, images: List[str], pipelines: dict, max_workers=None):
        """
        Use ProcessPoolExecutor for CPU-bound image transformations.
        """
        print(f"Running Parallel with {max_workers} workers...")
        start = time.time()
        
        tasks = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for img_path in images:
                for pipe_name, steps in pipelines.items():
                    # Submit task
                    future = executor.submit(
                        apply_pipeline_to_image, 
                        img_path, 
                        steps, 
                        self.output_dir, 
                        pipe_name
                    )
                    tasks.append(future)
            
            # Wait for completion
            for job in as_completed(tasks):
                res = job.result()
                if "Error" in str(res): print(res)
                
    def run_parallel_multiprocessing(self, images: List[str], pipelines: dict, max_workers=None):
        """
        Use multiprocessing.Pool for CPU-bound image transformations.
        """
        print(f"Running Parallel (Multiprocessing) with {max_workers} workers...")
        start = time.time()
        
        # Prepare arguments for starmap
        tasks = []
        for img_path in images:
            for pipe_name, steps in pipelines.items():
                tasks.append((img_path, steps, self.output_dir, pipe_name))
        
        with multiprocessing.Pool(processes=max_workers) as pool:
            results = pool.starmap(apply_pipeline_to_image, tasks)
            
            for res in results:
                if "Error" in str(res): print(res)
                
        print(f"Parallel (Multiprocessing) finished in {time.time() - start:.4f}s")


def load_pipelines_from_json(json_path: str) -> dict:
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Pipeline config file '{json_path}' not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}


if __name__ == "__main__":
    input_dir = "images"
    pipeline_config_file = "pipelines.json"
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        exit(1)

    # Get all image files from the input directory
    images = [
        os.path.join(input_dir, f) 
        for f in os.listdir(input_dir) 
        if os.path.splitext(f)[1].lower() in image_extensions
    ]

    if not images:
        print(f"No images found in '{input_dir}'")
        exit(0)

    print(f"Found {len(images)} images to process.")

    # Load pipelines from JSON
    pipelines = load_pipelines_from_json(pipeline_config_file)
    if not pipelines:
        print("No valid pipelines loaded. Exiting.")
        exit(1)

    processor = ImageProcessor("out")
    
    # processor.run_sequential(images, pipelines)
    # processor.run_parallel(images, pipelines, max_workers=10)
    processor.run_parallel_multiprocessing(images, pipelines, max_workers=10)


