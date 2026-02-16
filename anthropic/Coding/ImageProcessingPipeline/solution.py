import multiprocessing
import os
import json
from PIL import Image, ImageOps, ImageFilter

class ImageProcessor:
    def __init__(self, imagesDirPath, outputDirPath, pipelines):
        self.imagesDirPath = imagesDirPath
        self.outputDirPath = outputDirPath
        self.imageFiles = os.listdir(imagesDirPath)
        self.pipelines = pipelines

    def run_sequential(self):
        for imageFile in self.imageFiles:
            for name, pipeline in self.pipelines.items():
                self.apply_pipeline(imageFile, pipeline)

    def run_parallel(self):
        
        with multiprocessing.Pool(10) as p:
            for imageFile in self.imageFiles:
                for name, pipeline in self.pipelines.items():
                    p.apply_async(self.apply_pipeline, (imageFile, pipeline))
            p.close()
            p.join()


    def apply_pipeline(self, imageFile, pipeline):
        with open(os.path.join(self.imagesDirPath, imageFile), 'rb') as f:
            image = Image.open(f)
            operations = []
            for transform in pipeline:
                if transform["transform"] == "grayscale":
                    image = image.convert("L")
                elif transform["transform"] == "flip_horizontally":
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                elif transform["transform"] == "flip_vertically":
                    image = image.transpose(Image.FLIP_TOP_BOTTOM)
                elif transform["transform"] == "scale":
                    newSizes = (int(image.width * transform['args'][0]), int(image.height * transform['args'][0]))
                    image = image.resize(newSizes)
                elif transform["transform"] == "rotate":
                    image = image.rotate(transform["args"][0])
                elif transform["transform"] == "blur":
                    image = image.filter(ImageFilter.GaussianBlur(transform["args"][0]))
                
                operations.append(transform["transform"])

            processes = "_".join(operations)
            file_name, ext = os.path.splitext(imageFile)
            # Remove leading dot from ext if present for consistency, though splitting usually keeps it
            outputPath = os.path.join(self.outputDirPath, f"{file_name}_{processes}{ext}")
            image.save(outputPath)
            print(f"Saved {outputPath}")
        

if __name__ == "__main__":
    imagesDirPath = "images"
    outputDirPath = "out"
    print(os.getcwd())
    if not os.path.exists(outputDirPath):
        os.makedirs(outputDirPath)
        
    imageFiles = os.listdir(imagesDirPath)
    print(imageFiles)

    pipelinePath = "pipelines.json"

    with open(pipelinePath, 'r') as f:
        pipelines = json.load(f)
    print(pipelines)

    import time

    # Use a different variable name ('processor') to avoid shadowing the class 'ImageProcessor'
    processor = ImageProcessor(imagesDirPath, outputDirPath, pipelines)
    
    print("Running Sequential...")
    start_seq = time.time()
    processor.run_sequential()
    seq_time = time.time() - start_seq
    print(f"Sequential finished in {seq_time:.4f}s")
    
    print("Running Parallel...")
    start_par = time.time()
    processor.run_parallel()
    par_time = time.time() - start_par
    print(f"Parallel finished in {par_time:.4f}s")
    
    if seq_time > 0:
        print(f"Speedup: {seq_time / par_time:.2f}x")