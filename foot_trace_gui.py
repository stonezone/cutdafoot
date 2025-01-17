import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from pathlib import Path
import svgwrite
import logging
from datetime import datetime

class FootTraceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Foot Trace Processor")
        self.root.configure(bg='#333333')
        
        # Default parameters
        self.default_params = {
            'threshold': 128,         # Mid-point for black/white detection
            'simplification': 0.001,  # Good balance of detail/smoothness
            'stroke_width': 0.2       # Thin enough for clean laser cutting
        }
        
        # Current parameters (start with defaults)
        self.params = self.default_params.copy()
        
        self.setup_gui()
        self.setup_logging()
        
    def setup_logging(self):
        log_frame = ttk.LabelFrame(self.root, text="Process Log")
        log_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        self.log_widget = tk.Text(log_frame, height=6, width=60, bg='black', fg='white')
        self.log_widget.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        class TextHandler(logging.Handler):
            def __init__(self, widget):
                logging.Handler.__init__(self)
                self.widget = widget
            
            def emit(self, record):
                msg = self.format(record)
                self.widget.insert(tk.END, msg + '\n')
                self.widget.see(tk.END)
        
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = TextHandler(self.log_widget)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

    def setup_gui(self):
        # Create main frames
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        preview_frame = ttk.LabelFrame(self.root, text="Preview")
        preview_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Add parameter sliders with descriptions
        self.sliders = {}
        
        # Threshold slider
        slider_frame = ttk.Frame(control_frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(slider_frame, text="Threshold:").pack(anchor='w')
        ttk.Label(slider_frame, text="Higher = detect lighter marks", font=('Arial', 8)).pack(anchor='w')
        self.sliders['threshold'] = ttk.Scale(
            slider_frame, 
            from_=0, to=255, 
            value=self.params['threshold'],
            orient=tk.HORIZONTAL,
            command=self.update_preview)
        self.sliders['threshold'].pack(fill=tk.X)
        
        # Simplification slider
        slider_frame = ttk.Frame(control_frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(slider_frame, text="Simplification:").pack(anchor='w')
        ttk.Label(slider_frame, text="Higher = smoother outline", font=('Arial', 8)).pack(anchor='w')
        self.sliders['simplification'] = ttk.Scale(
            slider_frame, 
            from_=0.0001, to=0.01,
            value=self.params['simplification'],
            orient=tk.HORIZONTAL,
            command=self.update_preview)
        self.sliders['simplification'].pack(fill=tk.X)
        
        # Stroke width slider
        slider_frame = ttk.Frame(control_frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(slider_frame, text="SVG Stroke Width:").pack(anchor='w')
        ttk.Label(slider_frame, text="Higher = thicker line", font=('Arial', 8)).pack(anchor='w')
        self.sliders['stroke_width'] = ttk.Scale(
            slider_frame, 
            from_=0.1, to=5.0,  
            value=self.params['stroke_width'],
            orient=tk.HORIZONTAL,
            command=self.update_preview)
        self.sliders['stroke_width'].pack(fill=tk.X)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Open Image", 
                   command=self.open_image).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Reset to Defaults", 
                   command=self.reset_to_defaults).pack(side=tk.LEFT, padx=2)

        ttk.Button(button_frame, text="Generate SVG", 
                   command=self.generate_svg).pack(side=tk.LEFT, padx=2)
        
        # Preview canvases
        self.preview_original = tk.Canvas(preview_frame, width=300, height=400, bg='white')
        self.preview_original.grid(row=0, column=0, padx=5, pady=5)
        
        self.preview_processed = tk.Canvas(preview_frame, width=300, height=400, bg='white')  # White BG
        self.preview_processed.grid(row=0, column=1, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var).grid(
            row=1, column=0, columnspan=2, sticky="ew")

    def reset_to_defaults(self):
        for param, value in self.default_params.items():
            if param in self.sliders:
                self.sliders[param].set(value)
        self.update_preview()
        self.logger.info("Reset all settings to defaults")

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.current_image_path = file_path
            self.load_image(file_path)
        else:
            self.status_var.set("No file selected.")
            self.logger.warning("No file selected for image load.")

    def load_image(self, path):
        # Load and display original image
        try:
            image = Image.open(path)
            image.thumbnail((300, 400))
            self.photo = ImageTk.PhotoImage(image)
            self.preview_original.delete("all")
            self.preview_original.create_image(
                150, 200, image=self.photo, anchor=tk.CENTER)
            
            # Store OpenCV version for processing
            self.cv_image = cv2.imread(path)
            if self.cv_image is None:
                raise ValueError(f"Failed to load image from {path}")
            
            self.status_var.set(f"Image loaded: {Path(path).name}")
            self.logger.info(f"Image loaded: {Path(path).name}")
            
        except Exception as e:
            self.status_var.set(f"Error loading image: {str(e)}")
            self.logger.error(f"Error loading image: {str(e)}")
            self.cv_image = None

    def update_preview(self, *args):
        if not hasattr(self, 'cv_image') or self.cv_image is None:
            self.status_var.set("No image loaded for preview.")
            self.logger.warning("Attempted to update preview without an image.")
            return
            
        # Get current parameters from sliders
        for param in self.params:
            if param in self.sliders:
                self.params[param] = float(self.sliders[param].get())
        
        try:
            # Get contours and create preview image
            contours = self.get_contours(self.cv_image.copy())
            
            # Create preview image (white background)
            result = np.zeros_like(self.cv_image) + 255
            
            # Lowered this scale factor from 100 → 25 to get a thinner line at min
            preview_thickness = int(self.params['stroke_width'] * 25)
            if preview_thickness < 1:
                preview_thickness = 1
            
            cv2.drawContours(result, [contours], -1, (0, 0, 0), preview_thickness)
            
            # Convert to PIL format
            preview = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
            preview.thumbnail((300, 400))
            
            # Update preview
            self.preview_photo = ImageTk.PhotoImage(preview)
            self.preview_processed.delete("all")
            self.preview_processed.create_image(
                150, 200, image=self.preview_photo, anchor=tk.CENTER)
            
            self.status_var.set("Preview updated")
            self.logger.info("Preview updated with new settings")
            
        except Exception as e:
            self.status_var.set(f"Error updating preview: {str(e)}")
            self.logger.error(f"Preview update failed: {str(e)}")

    def get_contours(self, img):
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold (slider controls it directly)
        _, binary = cv2.threshold(
            gray,
            int(self.params['threshold']),
            255,
            cv2.THRESH_BINARY_INV
        )
        
        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and simplify contours
        valid_contours = [c for c in contours if cv2.contourArea(c) > 1000]
        if not valid_contours:
            raise ValueError("No valid contours found")
        
        largest = max(valid_contours, key=cv2.contourArea)
        epsilon = self.params['simplification'] * cv2.arcLength(largest, True)
        return cv2.approxPolyDP(largest, epsilon, True)

    def generate_svg(self):
        if not hasattr(self, 'cv_image') or self.cv_image is None:
            self.status_var.set("No image loaded")
            return
            
        try:
            # Get contours
            simplified = self.get_contours(self.cv_image)
            
            # Create SVG
            output_path = Path(self.current_image_path).with_suffix('.svg')
            height, width = self.cv_image.shape[:2]
            dwg = svgwrite.Drawing(str(output_path), size=(width, height))
            
            # Convert contour to path
            path_data = "M"
            for point in simplified.squeeze():
                path_data += f" {point[0]},{point[1]}"
            path_data += " Z"
            
            # Add path to SVG (keeps original param so actual file is still quite thin at 0.1)
            dwg.add(dwg.path(
                d=path_data,
                stroke='black',
                fill='none',
                stroke_width=str(self.params['stroke_width'])
            ))
            
            # Save SVG
            dwg.save()
            
            self.status_var.set(f"SVG saved: {output_path}")
            self.logger.info(f"Generated SVG: {output_path}")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.logger.error(f"SVG generation failed: {str(e)}")

def main():
    root = tk.Tk()
    app = FootTraceGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()