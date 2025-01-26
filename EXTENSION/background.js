

// chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
//     if (request.url) {
//         console.log("Received image URL for OCR:", request.url);  // Debugging: log the URL received
//         sendImageToOCR(request.url);  // Send the image directly to the OCR API
//     }
// });

// async function sendImageToOCR(imageUrl, originalFileName) {
//     console.log("Sending image to OCR model:", originalFileName); // Debugging: log the filename sent to OCR

//     const formData = new FormData();

//     try {
//         const response = await fetch(imageUrl);
//         if (!response.ok) {
//             console.error("Failed to fetch image from URL:", imageUrl);
//             return; // Exit if the fetch fails
//         }

//         const blob = await response.blob();
//         formData.append('file', blob, originalFileName);

//         const ocrResponse = await fetch('http://127.0.0.1:5001/predict', {
//             method: 'POST',
//             body: formData
//         });

//         if (!ocrResponse.ok) {
//             console.error("Failed to send image to OCR:", ocrResponse.statusText);
//             return; // Exit if the OCR request fails
//         }

//         const data = await ocrResponse.json();
//         if (data.predicted_text) {
//             console.log("OCR Result:", data.predicted_text);
//             // Send the OCR result to the content script
//             chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
//                 chrome.tabs.sendMessage(tabs[0].id, { type: 'OCR_RESULT', text: data.predicted_text });
//             });
//         } else {
//             console.error("No text found in OCR result");
//         }
//     } catch (error) {
//         console.error("Error sending image to OCR:", error);
//     }
// }

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.url) {
        console.log("Received image URL for OCR:", request.url);
        sendImageToOCR(request.url, request.filename || "captcha.png");
    } else if (request.dataURL) {
        console.log("Received canvas data URL for OCR");
        sendImageToOCR(request.dataURL, request.filename || "canvas_captcha.png", true);
    }
});

async function sendImageToOCR(imageSource, originalFileName, isDataURL = false) {
    console.log("Sending image to OCR model:", originalFileName);

    const formData = new FormData();

    try {
        let blob;

        if (isDataURL) {
            // Convert dataURL to Blob
            const byteString = atob(imageSource.split(',')[1]);
            const mimeString = imageSource.split(',')[0].split(':')[1].split(';')[0];
            const byteArray = new Uint8Array(byteString.length);
            for (let i = 0; i < byteString.length; i++) {
                byteArray[i] = byteString.charCodeAt(i);
            }
            blob = new Blob([byteArray], { type: mimeString });
        } else {
            // Fetch the image from the URL
            const response = await fetch(imageSource);
            if (!response.ok) {
                console.error("Failed to fetch image from URL:", imageSource);
                return;
            }
            blob = await response.blob();
        }

        formData.append('file', blob, originalFileName);

        const ocrResponse = await fetch('http://127.0.0.1:5001/predict', {
            method: 'POST',
            body: formData
        });

        if (!ocrResponse.ok) {
            console.error("Failed to send image to OCR:", ocrResponse.statusText);
            return;
        }

        const data = await ocrResponse.json();
        if (data.predicted_text) {
            console.log("OCR Result:", data.predicted_text);

            // Send the OCR result to the content script
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.tabs.sendMessage(tabs[0].id, { type: 'OCR_RESULT', text: data.predicted_text });
            });
        } else {
            console.error("No text found in OCR result");
        }
    } catch (error) {
        console.error("Error sending image to OCR:", error);
    }
}
