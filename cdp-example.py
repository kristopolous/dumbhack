'use strict';

const puppeteer = require('puppeteer-core');

(async () => {
  try {
    // Use browserWSEndpoint to pass the Lightpanda's CDP server address.
    const browser = await puppeteer.connect({
      browserWSEndpoint: "ws://127.0.0.1:9222",
    });

    // The rest of your script remains the same.
    const context = await browser.createBrowserContext();
    const page = await context.newPage();

    // Get the URL from the command line arguments
    const url = process.argv[2];

    if (!url) {
      console.error('Please provide a URL as a command line argument.');
      process.exit(1);
    }

    // Dump all the links from the page.
    await page.goto(url);

    const links = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('a')).map(row => {
        const href = row.getAttribute('href');
        return href;
      });
    });

    console.log(JSON.stringify(links));

    await page.close();
    await context.close();
    await browser.disconnect();
  } catch (error) {
    console.error("An error occurred:", error);
  }
})();;
