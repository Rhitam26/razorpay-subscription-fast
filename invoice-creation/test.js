const puppeteer = require('puppeteer');

async function convertHTMLToPDF(htmlContent, outputPath) {
    try {
        // Launch the browser
        const browser = await puppeteer.launch({
            headless: 'new' // Use new headless mode
        });

        // Create a new page
        const page = await browser.newPage();

        // Set the content of the page
        await page.setContent(htmlContent, {
            waitUntil: 'networkidle0' // Wait until network is idle
        });

        // Generate PDF
        await page.pdf({
            path: outputPath,
            format: 'A4',
            margin: {
                top: '20px',
                right: '20px',
                bottom: '20px',
                left: '20px'
            },
            printBackground: true
        });

        // Close the browser
        await browser.close();

        console.log(`PDF has been created successfully at: ${outputPath}`);
    } catch (error) {
        console.error('Error generating PDF:', error);
    }
}

// Example usage
const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
    <style>
        body { font-family: Arial, sans-serif; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a test document.</p>
</body>
</html>
`;

convertHTMLToPDF(html, 'output.pdf');