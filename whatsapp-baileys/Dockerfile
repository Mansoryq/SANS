FROM node:20-alpine

WORKDIR /app

# Install dependencies for canvas/puppeteer if needed by Baileys, though mostly it's pure JS.
# Sometimes python/make is needed for native modules.
RUN apk add --no-cache python3 make g++ 

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
