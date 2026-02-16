import os
from PIL import Image, ImageOps, ImageFilter

class LargeImageProcessor:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_large_image(self, input_path, tile_size=(1024, 1024)):
        """
        Processes an image larger than RAM by breaking it into tiles.
        """
        filename = os.path.splitext(os.path.basename(input_path))[0]
        
        # 1. Open lazily (does not load pixels)
        with Image.open(input_path) as img:
            width, height = img.size
            print(f"Processing oversized image: {width}x{height}")

            # 2. Iterate over the image in chunks (tiles)
            for y in range(0, height, tile_size[1]):
                for x in range(0, width, tile_size[0]):
                    
                    # Define the box for the current tile
                    # box = (left, upper, right, lower)
                    box = (
                        x, 
                        y, 
                        min(x + tile_size[0], width), 
                        min(y + tile_size[1], height)
                    )
                    
                    # 3. Load ONLY this region into RAM
                    tile = img.crop(box)
                    
                    # 4. Apply your pipeline to this small tile
                    processed_tile = self.apply_pipeline_to_tile(tile)
                    
                    # 5. Save tile immediately and free RAM
                    tile_name = f"{filename}_tile_{x}_{y}.jpg"
                    save_path = os.path.join(self.output_dir, tile_name)
                    processed_tile.save(save_path)
                    print(f"Saved tile: {tile_name}")
                    
                    # Explicitly delete to free memory (optional in Python but good practice here)
                    del tile
                    del processed_tile

    def apply_pipeline_to_tile(self, tile_img):
        """
        Apply standard operations to a single tile.
        NOTE: Operations likely blur or rotate need special handling (overlap)
        to avoid seams at tile edges.
        """
        # Example: Grayscale is safe (pixel-independent)
        tile_img = ImageOps.grayscale(tile_img)
        
        # Example: Flip is safe if you flip the tile coordinates too
        # tile_img = ImageOps.mirror(tile_img) 
        
        return tile_img

if __name__ == "__main__":
    # Create a dummy "large" image for testing
    input_img = "huge_test.jpg"
    img = Image.new('RGB', (4000, 4000), color='red') # Imagine this is 100GB
    img.save(input_img)

    processor = LargeImageProcessor("out_tiles")
    processor.process_large_image(input_img, tile_size=(1000, 1000))
