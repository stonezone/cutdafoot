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
        
        self.default_params = {
            'threshold': 128,
            'simplification': 0.001,
            'stroke_width': 0.2
        }
        self.params = self.default_params.copy()
        
        self.setup_gui()
        self.setup_logging()
        
    def setup_logging(self):
        log_frame = ttk.LabelFrame(self.root, text="Process Log")
        log_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
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
        main_frame = ttk.LabelFrame(self.root, text="Controls")
        main_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Threshold slider
        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(slider_frame, text="Threshold:").pack(anchor='w')
        ttk.Label(slider_frame, text="Higher = detect lighter marks", font=('Arial', 8)).pack(anchor='w')
        self.threshold_slider = ttk.Scale(
            slider_frame, 
            from_=0, to=255, 
            value=self.params['threshold'],
            orient=tk.HORIZONTAL)
        self.threshold_slider.pack(fill=tk.X)
        
        # Simplification slider
        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(slider_frame, text="Simplification:").pack(anchor='w')
        ttk.Label(slider_frame, text="Higher = smoother outline", font=('Arial', 8)).pack(anchor='w')
        self.simplification_slider = ttk.Scale(
            slider_frame, 
            from_=0.0001, to=0.01,
            value=self.params['simplification'],
            orient=tk.HORIZONTAL)
        self.simplification_slider.pack(fill=tk.X)
        
        # Stroke width slider
        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(slider_frame, text="SVG Stroke Width:").pack(anchor='w')
        ttk.Label(slider_frame, text="Higher = thicker line", font=('Arial', 8)).pack(anchor='w')
        self.stroke_slider = ttk.Scale(
            slider_frame, 
            from_=0.1, to=1.0,
            value=self.params['stroke_width'],
            orient=tk.HORIZONTAL)
        self.stroke_slider.pack(fill=tk.X)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Open Image", 
                  command=self.open_image).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_to_defaults).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Generate SVG", 
                  command=self.generate_svg).pack(side=tk.LEFT, padx=2)

        # Original image preview
        self.preview = tk.Canvas(main_frame, width=300, height=400, bg='white')
        self.preview.pack(padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var).grid(
            row=2, column=0, sticky="ew")

    def reset_to_defaults(self):
        self.threshold_slider.set(self.default_params['threshold'])
        self.simplification_slider.set(self.default_params['simplification'])
        self.stroke_slider.set(self.default_params['stroke_width'])
        self.logger.info("Reset to defaults")

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.current_image_path = file_path
            image = Image.open(file_path)
            image.thumbnail((300, 400))
            self.photo = ImageTk.PhotoImage(image)
            self.preview.delete("all")
            self.preview.create_image(150, 200, image=self.photo, anchor=tk.CENTER)
            self.cv_image = cv2.imread(file_path)
            self.logger.info(f"Opened image: {Path(file_path).name}")

    def generate_svg(self):
        if not hasattr(self, 'cv_image'):
            self.status_var.set("No image loaded")
            return
            
        try:
            # Update parameters from sliders
            self.params['threshold'] = self.threshold_slider.get()
            self.params['simplification'] = self.simplification_slider.get()
            self.params['stroke_width'] = self.stroke_slider.get()
            
            # Process image
            gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(
                gray,
                int(self.params['threshold']),
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            # Find contours
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            valid_contours = [c for c in contours 
                            if cv2.contourArea(c) > 1000]
            if not valid_contours:
                raise ValueError("No valid contours found")
            
            largest = max(valid_contours, key=cv2.contourArea)
            epsilon = self.params['simplification'] * cv2.arcLength(largest, True)
            simplified = cv2.approxPolyDP(largest, epsilon, True)
            
            # Create SVG
            output_path = Path(self.current_image_path).with_suffix('.svg')
            height, width = self.cv_image.shape[:2]
            dwg = svgwrite.Drawing(str(output_path), size=(width, height))
            
            # Convert contour to path
            path_data = "M"
            for point in simplified.squeeze():
                path_data += f" {point[0]},{point[1]}"
            path_data += " Z"
            
            # Add path to SVG
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