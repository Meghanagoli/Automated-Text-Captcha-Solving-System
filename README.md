
# Automated text CAPTCHA Solving System


## Overview  
CAPTCHAs are critical for online security, protecting websites from spam, bots, and unauthorized access. However, solving them repeatedly can be tedious, especially for users with disabilities.  

This project introduces a **Chrome extension** that automates CAPTCHA solving using advanced **OCR models** powered by machine learning. With seamless integration and real-time processing, the tool enhances accessibility, usability, and efficiency without compromising security.  

---

## Key Features  
- **Automated CAPTCHA Solving**: Automatically detects, interprets, and solves CAPTCHAs on web pages.  
- **Real-Time Performance**: Integrates with a browser for real-time CAPTCHA resolution.  
- **High Accuracy OCR**: Utilizes CNN + Bidirectional LSTM models to decode distorted CAPTCHA text.  
- **User-Friendly Interface**: Simple Chrome extension with voice feedback for accessibility.  
- **Accessibility Enhancements**: Helps users with visual impairments or limited mobility.  

---

## Technologies Used  
- **Programming Languages**:  
  - Python (Backend and OCR Models)  
  - JavaScript, HTML, CSS (Chrome Extension)  
- **Libraries/Frameworks**:  
  - TensorFlow, Keras, OpenCV (OCR Implementation)  
  - Flask (Backend API)  
- **Browser**: Chrome Extension Framework  

---

## Installation  

### Prerequisites  
1. **Python** (Version 3.8 or higher).  
2. **Google Chrome** (Latest version).  

### Steps  
1. **Clone the repository**:  
   ```bash  
   git clone https://github.com/username/captcha-solver.git  
   cd captcha-solver  
   ```  
2. **Train model with your dataset**:  
   -Replace dataset folder names

   ```bash  
   python train.py  
   ```  
   -Models will be saved in folder "Models"
3. **Set up the Chrome extension**:  
   - Open Chrome and navigate to `chrome://extensions`.  
   - Enable **Developer mode** (toggle in the top-right).  
   - Click on **Load unpacked** and select the `extension` folder in the repository.  

4. **Start the backend server**:  
   ```bash  
   python server.py  
   ```  

5. **Use the extension**:  
   - Open any CAPTCHA-protected webpage.  
   - Click the "Solve" button in the extension popup.  

---

## Workflow  

1. **Data Collection**: Captures CAPTCHA images from various government and secure websites for training.  
2. **Preprocessing**: Normalizes and prepares CAPTCHA images for OCR.  
3. **Model Training**: CNN + Bidirectional LSTM model predicts text from CAPTCHA images with high accuracy.  
4. **Chrome Extension**: Bridges the backend model with real-time CAPTCHA solving.  

---

## Results  

| **Metric**          | **Numeric OCR Model** | **Alphanumeric OCR Model** |  
|----------------------|-----------------------|-----------------------------|  
| Accuracy (%)         | 95.1                 | 97.7                        |  
| Precision (%)        | 98.1                 | 98.1                        |  
| F1 Score (%)         | 98.1                 | 98.1                        |  

- Outperformed industry-standard OCR tools (Tesseract, PaddleOCR) in accuracy and efficiency.  
- Real-time CAPTCHA solving reduces user effort by over 90%.  

---


