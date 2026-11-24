FROM mcr.microsoft.com/playwright:v1.65.1-noble
WORKDIR /e2e
COPY package.json ./
RUN npm install
# Browsers are pre-installed in the image — make sure versions align
RUN npx playwright install chromium
COPY . .
