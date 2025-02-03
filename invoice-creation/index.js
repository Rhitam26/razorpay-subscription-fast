const fs = require('fs');
const AWS = require('aws-sdk');
const express = require('express')
const bodyParser = require('body-parser');
const serveless = require('serverless-http')
const puppeteer = require("puppeteer");
// import enviornment variables
require('dotenv').config();



// get the enviornment variables    
const region = process.env.REGION;
const accessKeyId = process.env.ACCESS_KEY;
const secretAccessKey = process.env.SECRET_KEY;





AWS.config.update({
    region: region, // Replace with your AWS region
    accessKeyId: accessKeyId, // Replace with your AWS access key
    secretAccessKey: secretAccessKey // Replace with your AWS secret key
});

const s3 = new AWS.S3();


function generateHtml(paymentDetails) {
        const logoBase64 = fs.readFileSync('logo-black-large.png', { encoding: 'base64' });
    return `
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #F8F8F8;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #E6F3E6;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 20px;
        }
        .header img {
            height: 40px;
        }
        .header .title {
            font-size: 18px;
            font-weight: bold;
        }
        .Invoice {
            margin-bottom: 20px;
            text-align: center;
        }
        .Invoice h1 {
            font-size: 36px;
            margin: 0;
            padding: 20px 10px;
        }
        .Invoice .logo-title-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 20px;
        }
        .Invoice .logo-title-container img {
            margin-bottom: 15px;
        }
        .Invoice .amount {
            font-size: 36px;
            color: #333;
        }
        .details {
            margin-bottom: 30px;
            text-align: center;
        }
        .details div {
            margin-bottom: 8px;
        }
        .table_block {
            font-size: 16px;
            margin: 0 auto;
            max-width: 600px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .table_block td {
            padding: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="Invoice">
            <h1>Invoice from Prima Stat</h1>
            <div class="logo-title-container">
                <img src="data:image/png;base64,${logoBase64}" alt="Logo" style="height: 60px; width: 120px;">
                <div class="title">Invoice</div>
            </div>

            <div class="amount">${paymentDetails.currency} ${paymentDetails.totalAmount}</div>
            <div>Paid ${paymentDetails.amountPayed}</div>
        </div>
      
        <div class="details">
            <div>Invoice number: ${paymentDetails.invoiceNumber}</div>
        </div>

        <table class="table_block" width="100%" border="0" cellpadding="0" cellspacing="0">
            <tbody>
                <tr>
                    <td width="50%">Invoice</td>
                    <td width="50%" align="right">${paymentDetails.payemntPeriod}</td>
                </tr>    
                <tr>
                    <td width="50%">${paymentDetails.product}</td>
                    <td width="50%" align="right">${paymentDetails.currency} ${paymentDetails.productCost}</td>
                </tr>
                <tr>
                    <td width="50%">Qty</td>
                    <td width="50%" align="right">${paymentDetails.productQuantity}</td>
                </tr>
                <tr>
                    <td width="50%">Total</td>
                    <td width="50%" align="right">${paymentDetails.currency} ${paymentDetails.totalAmount}</td>
                </tr>
                <tr>
                    <td width="50%">Amount paid</td>
                    <td width="50%" align="right">${paymentDetails.currency} ${paymentDetails.amountPayed}</td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>


    `;
}

// async function createPdf(htmlContent, outputPath) {
    
//     // Launch Puppeteer using chrome-aws-lambda
//     const browser = await puppeteer.launch({
//         args: chromium.args,
//       defaultViewport: chromium.defaultViewport,
//       executablePath: await chromium.executablePath,
//       headless: chromium.headless,
//       ignoreHTTPSErrors: true,
//     });
//     const page = await browser.newPage();
//     await page.setContent(htmlContent, { waitUntil: "load" });
//     const pdfBuffer = await page.pdf({ format: "A4" });
//     await browser.close();
//     // Write the PDF buffer to a file
//     fs.writeFileSync(outputPath, pdfBuffer);
//     console.log('PDF generated successfully');


// }


async function createPdf(htmlContent, outputPath) {
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



async function uploadToS3(filePath, bucketName, key) {
    const fileContent = fs.readFileSync(filePath);
    const params = {
        Bucket: bucketName,
        Key: key,
        Body: fileContent,
        ContentType: 'application/pdf'
    };

    try {
        const data = await s3.upload(params).promise();
        console.log(`File uploaded successfully at ${data.Location}`);
        return data.Location;
    } catch (err) {
        console.error('Error uploading file:', err);
    }
}

// create an api that takes payment details

const app = express();

app.use(bodyParser.json());

app.post('/generate-pdf', async (req, res) => {
    const paymentDetails = req.body;

    try {
        const html = generateHtml(paymentDetails);
        console.log(html);
        const outputPath = './receipt.pdf'; // Temporary file path for the PDF

        // Generate PDF
        await createPdf(html, outputPath);

        // Upload PDF to S3
        // const bucketName = process.env.BUCKET;
        // // unix time stamp of the day
        // const timeStamp = (new Date().getTime()).toString();
  
       
        const key = `invoice/${paymentDetails.customerName.replace(/\s+/g, '_')} - ${timeStamp}.pdf`;
        const fileLocation = await uploadToS3(outputPath, bucketName, key);

       const response = {
            message: 'PDF generated and uploaded successfully',
            location: fileLocation
        };
        res.json(response);

    } catch (error) {
        console.error('Error:', error);
        res.status(500).send('Internal Server Error');
    }
});



const PORT = process.env.PORT || 3030;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

app.get('/', (req, res) => {
    res.send('Hello World!');
});

module.exports.handler = serveless(app);