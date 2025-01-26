

console.log("Extension started");

let downloadedImages = new Set(); // To keep track of already downloaded images

// Function to play sound
function playSound() {
    const audio = new Audio(chrome.runtime.getURL("assets/audio.mp3")); // Ensure success.mp3 is in your extension's assets folder
    audio.play();
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "extractCaptchas") {
        detectCaptcha();
    }
});

function detectCaptcha() {
    console.log("Starting CAPTCHA extraction...");
    const canvasCaptcha = document.querySelector('canvas#captchaCanvas');
    if (canvasCaptcha) {
        console.log("Detected CAPTCHA in <canvas> element.");

        const canvasDataURL = canvasCaptcha.toDataURL("image/png");

        if (!downloadedImages.has(canvasDataURL)) {
            downloadedImages.add(canvasDataURL);

            const filename = "canvas_captcha.png";

            chrome.runtime.sendMessage({
                dataURL: canvasDataURL,
                filename: filename
            }, response => {
                if (response?.status === "success") {
                    console.log(`Canvas CAPTCHA sent successfully with filename: ${filename}`);
                } else {
                    console.error("Failed to send canvas CAPTCHA to the background script.");
                }
            });
        }
    }

    const captchaBox = document.querySelector('.pvc-form__captcha-box');

    if (captchaBox) {
        const images = captchaBox.querySelectorAll('img');
        if (images.length === 0) {
            console.log("No CAPTCHA image found within .pvc-form__captcha-box.");
            return;
        }

        for (let img of images) {
            const imgSrc = img.src;

            if (!downloadedImages.has(imgSrc)) {
                console.log('Detected CAPTCHA image:', imgSrc);
                downloadedImages.add(imgSrc);

                const inputField = document.querySelector('input[name="captcha"]');
                const filename = inputField.value || "Captcha.png";

                chrome.runtime.sendMessage({
                    url: imgSrc,
                    filename: filename
                });
                break;
            }
        }
    }

    const images = document.querySelectorAll('img[title="Image CAPTCHA"],img[class*="pvc-form__captcha-box"],img[class*="captcha-img"],img[alt="Captcha"],img[id="ctl00_OnlineContent_imgCaptcha"],img[alt="Image Source"], img[alt*="captcha"], img[id="captcha"],img[id="imageCaptcha"],img[id="mobileCaptchaImage"],img[id="ctl00_OnlineContent_imgCaptcha"],img[id="ctl00_ContentPlaceHolder1_imgCaptcha"],img[id="ctl00_PlaceHolderMain_loginDGET_LoginDGET_Captcha_ImgCaptha"] ,img[id="my-captcha-image-image"]');
    console.log(`Found ${images.length} images matching criteria.`);

    if (images.length === 0) {
        console.log("No CAPTCHA image found with alt='Captcha' or related attributes.");
        return;
    }

    for (let img of images) {
        const imgSrc = img.src;

        if (!downloadedImages.has(imgSrc)) {
            console.log('Detected CAPTCHA image:', imgSrc);
            downloadedImages.add(imgSrc);

            chrome.runtime.sendMessage({ url: imgSrc });
            break;
        }
    }
}

// chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//     if (message.type === 'OCR_RESULT') {
//         // playSound();
//         const inputField = document.querySelector('input[name="captcha"]') || 
//             document.querySelector('input[name="ctl00$OnlineContent$txtCaptcha"]') ||  
//             document.querySelector('input[name="ctl00$ContentPlaceHolder1$txtCaptcha"]') ||
//             document.querySelector('input[name="captcha_response"]') || 
//             document.querySelector('input[name*="verifycode"], input[id*="captcha"]') ||
//             document.querySelector('input[formcontrolname="captchForm"]') ||
//             document.querySelector('input[id="txtInput"]') ||
//             document.querySelector('input[id="my-captcha-image"]'); // Replace with the correct ID or class
        
//         if (inputField) {
//             inputField.value = message.text;  // Set the OCR result in the input field
            
//             // Play sound after solving CAPTCHA
//             playSound();
//         }
//     }
// });

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'OCR_RESULT') {
        // Play sound function (if needed)
       

        // Select the appropriate input field
        const inputField = document.querySelector('input[name="captcha"]') || 
            document.querySelector('input[name="ctl00$OnlineContent$txtCaptcha"]') ||  
            document.querySelector('input[name="ctl00$ContentPlaceHolder1$txtCaptcha"]') ||
            document.querySelector('input[name="captcha_response"]') || 
            document.querySelector('input[name*="verifycode"], input[id*="captcha"]') ||
            document.querySelector('input[formcontrolname="captchForm"]') ||
            document.querySelector('input[id="txtInput"]') ||
            document.querySelector('input[id="my-captcha-image"]'); // Replace with the correct ID or class

        if (inputField) {
            const text = message.text; // OCR result
            const typingSpeed = 120; // Typing speed in milliseconds

            // Typing effect function
            let index = 0;
            const type = () => {
                if (index < text.length) {
                    inputField.value += text[index]; // Add character by character
                    index++;
                    setTimeout(type, typingSpeed);
                    
                } else {
                    // Play sound after typing completes
                    playSound();
                }
            };

            type(); // Start typing effect
        }
    }
});
