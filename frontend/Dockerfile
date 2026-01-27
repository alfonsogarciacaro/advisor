FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Expose Next.js dev server port
EXPOSE 3000

CMD ["npm", "run", "dev"]
