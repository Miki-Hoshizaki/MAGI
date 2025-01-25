document.addEventListener('DOMContentLoaded', () => {
    // Get the ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    
    if (!id) {
        document.getElementById('result-container').innerHTML = 'Error: No ID provided in URL';
        return;
    }

    const resultContainer = document.getElementById('result-container');
    const decoder = new TextDecoder();
    let lastContent = '';

    // Function to format text
    function formatText(text) {
        text = text.replace(/(&lt;inner_monologue&gt;)/g, '<span class="tag-like">$1</span>');
        text = text.replace(/(&lt;\/inner_monologue&gt;)/g, '<span class="tag-like">$1</span>');
        text = text.replace(/(&lt;reasoning&gt;)/g, '<span class="tag-like">$1</span>');
        text = text.replace(/(&lt;\/reasoning&gt;)/g, '<span class="tag-like">$1</span>');

        // Format POSITIVE and NEGATIVE
        text = text.replace(/POSITIVE/g, '<span class="positive-local">POSITIVE</span>');
        text = text.replace(/NEGATIVE/g, '<span class="negative-local">NEGATIVE</span>');
        
        let lines = text.split('\n');
        
        lines = lines.map(line => {
            // Format numbered titles (e.g., "1. Layered Architecture:") if it's at the start of a line
            if (/^\d+\.\s+[^:]+:/.test(line)) {
                line = line.replace(/^(\d+\.\s+[^:]+:)/, '<span class="numbered-title">$1</span>');
            }
            return line;
        });
        
        return lines.join('\n');
    }

    // Function to check completion
    function isCompleted(text) {
        return text.includes('COMPLETED') || text.includes('ERROR');
    }

    // Function to stream the response
    async function streamResponse() {
        while (true) {
            try {
                const response = await fetch(`http://127.0.0.1:8000/v1/results/${id}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const text = await response.text();
                
                // Only update if content has changed
                if (text !== lastContent) {
                    resultContainer.innerHTML = formatText(text);
                    lastContent = text;
                    
                    // If completed, stop polling
                    if (isCompleted(text)) {
                        break;
                    }
                }
                
                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, 1000));
                
            } catch (error) {
                resultContainer.innerHTML = `Error: ${error.message}`;
                break;
            }
        }
    }

    // Start streaming
    streamResponse();
});
