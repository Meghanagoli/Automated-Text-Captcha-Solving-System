


document.getElementById('extract-captcha').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
            chrome.tabs.sendMessage(tabs[0].id, { action: "extractCaptchas" }, (response) => {
                if (chrome.runtime.lastError) {
                    //console.error("Error sending message:", chrome.runtime.lastError.message);
                } else {
                    console.log("Message sent successfully:", response);
                    // Display predicted text in the popup
                    if (response && response.predictedText) {
                        document.getElementById('predicted-text').textContent = `Predicted Text: ${response.predictedText}`;
                        // Optionally, you can send the predicted text to the webpage as well
                        chrome.tabs.executeScript(tabs[0].id, {
                            code: `document.body.innerHTML += "<div>Predicted Text: ${response.predictedText}</div>";`
                        });
                    } else {
                        console.log("No predicted text received.");
                    }
                }
            });
        } else {
            console.error("No active tab found.");
        }
    });
});



